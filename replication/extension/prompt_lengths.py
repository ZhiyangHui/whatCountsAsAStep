"""Lower-bound historical ASCII-serialized user messages using the Qwen GGUF vocabulary."""
import argparse
import csv
import hashlib
import json
import struct
from pathlib import Path


def vocabulary(path):
    with path.open('rb') as f:
        def integer(fmt):
            return struct.unpack('<' + fmt, f.read(struct.calcsize('<' + fmt)))[0]

        def string():
            return f.read(integer('Q')).decode()

        def value(kind):
            if kind == 8:
                return string()
            if kind == 9:
                subtype = integer('I')
                return [value(subtype) for _ in range(integer('Q'))]
            return integer({0:'B', 1:'b', 2:'H', 3:'h', 4:'I', 5:'i', 6:'f',
                            7:'?', 10:'Q', 11:'q', 12:'d'}[kind])

        assert f.read(4) == b'GGUF' and integer('I') == 3
        integer('Q')
        for _ in range(integer('Q')):
            key = string()
            result = value(integer('I'))
            if key == 'tokenizer.ggml.tokens':
                return result
    raise ValueError('Vocabulary missing')


def token_trie(tokens):
    # GPT-2 byte alphabet: visible bytes retain their code point.
    visible = list(range(33, 127)) + list(range(161, 173)) + list(range(174, 256))
    hidden = [b for b in range(256) if b not in visible]
    decode = {chr(b): b for b in visible}
    decode.update({chr(256+i): b for i,b in enumerate(hidden)})
    trie = {}
    for token in tokens:
        if not token or any(decode.get(c,256)>127 for c in token):
            continue
        node = trie
        for c in token:
            node = node.setdefault(decode[c], {})
        node[None] = True
    return trie


def minimum(text, trie):
    data = text.encode('ascii')
    size = len(data)
    costs = [size+1]*(size+1)
    costs[0] = 0
    for start in range(size):
        node = trie
        for j in range(start,size):
            node = node.get(data[j])
            if node is None:
                break
            if None in node:
                costs[j+1] = min(costs[j+1], costs[start]+1)
    assert costs[size] <= size
    return costs[size]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('gguf','receipts','calls','output'):
        parser.add_argument(key,type=Path)
    args = parser.parse_args()
    trie = token_trie(vocabulary(args.gguf))
    with args.receipts.open() as source, args.output.open('w',newline='') as dest:
        writer = csv.writer(dest)
        writer.writerow(['id','payload_sha256','minimum_user_tokens','prompt_eval_count','num_ctx'])
        for row in csv.DictReader(source):
            digest = row['payload_sha256']
            log = json.loads((args.calls/(digest+'.json')).read_bytes())
            req = log['request']
            assert hashlib.sha256(json.dumps(req,sort_keys=True).encode()).hexdigest()==digest
            count = log['response']['prompt_eval_count']
            assert count == int(row['prompt_eval_count'])
            writer.writerow([row['id'],digest,minimum(req['messages'][1]['content'],trie),count,req['options']['num_ctx']])
