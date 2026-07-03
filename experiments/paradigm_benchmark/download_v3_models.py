"""下载多语言 embedding 模型到本地缓存。"""
import os
import sys

os.environ['HF_HOME'] = 'd:/hf_cache'

CACHE = 'd:/hf_cache'

MODELS = [
    'BAAI/bge-small-en-v1.5',          # ~95 MB, 384 维
    'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',  # ~470 MB, 384 维
    'Helsinki-NLP/opus-mt-zh-en',      # ~300 MB, 翻译 zh→en
]

try:
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    print('NEED sentence_transformers:', e); sys.exit(1)

for m in MODELS:
    try:
        if 'opus-mt' in m:
            from transformers import MarianMTModel, MarianTokenizer
            tok = MarianTokenizer.from_pretrained(m, cache_dir=CACHE)
            model = MarianMTModel.from_pretrained(m, cache_dir=CACHE)
            print(f'OK  {m}  (translator)')
            del model, tok
        else:
            model = SentenceTransformer(m, device='cpu', cache_folder=CACHE)
            try:
                dim = model.get_embedding_dimension()
            except AttributeError:
                dim = model.get_sentence_embedding_dimension()
            print(f'OK  {m}  dim={dim}')
            del model
    except Exception as e:
        print(f'FAIL {m}: {type(e).__name__}: {str(e)[:150]}')
