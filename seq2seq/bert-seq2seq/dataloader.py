"""

@file  : dataloader.py

@author: xiaolu

@time  : 2020-03-25

"""
import torch
import pandas as pd
from torch.utils.data.dataset import Dataset
from tokenizer import load_bert_vocab, Tokenizer
from config import Config


def read_corpus(data_path):
    """
    读原始数据
    """
    df = pd.read_csv(data_path, delimiter="\t")
    sents_src = []
    sents_tgt = []
    for index, row in df.iterrows():
        data_json = eval(row[0])
        dream = data_json["dream"]
        decode = data_json["decode"]
        sents_src.append(dream)
        sents_tgt.append(decode)
    return sents_src, sents_tgt


class DreamDataset(Dataset):
    """
    自定义dataset
    针对周公姐解梦数据集，定义一个相关的取数据的方式
    """
    def __init__(self):
        # 一般init函数是加载所有数据
        super(DreamDataset, self).__init__()
        # 读原始数据
        self.sents_src, self.sents_tgt = read_corpus(Config.dream_train_corpus_path)
        self.word2idx = load_bert_vocab()
        self.idx2word = {k: v for v, k in self.word2idx.items()}
        self.tokenizer = Tokenizer(self.word2idx)

    def __getitem__(self, i):
        # 得到单个数据
        src = self.sents_src[i]
        tgt = self.sents_tgt[i]

        token_ids, token_type_ids = self.tokenizer.encode(src, tgt)
        output = {
            "token_ids": token_ids,
            "token_type_ids": token_type_ids,
        }
        return output

    def __len__(self):
        return len(self.sents_src)


def collate_fn(batch):
    """
    动态padding， batch为一部分sample
    """
    def padding(indice, max_length, pad_idx=0):
        """
        pad 函数
        注意 token type id 右侧pad是添加1而不是0，1表示属于句子B
        """
        pad_indice = [item + [pad_idx] * max(0, max_length - len(item)) for item in indice]
        return torch.tensor(pad_indice)

    token_ids = [data["token_ids"] for data in batch]
    max_length = max([len(t) for t in token_ids])
    token_type_ids = [data["token_type_ids"] for data in batch]

    token_ids_padded = padding(token_ids, max_length)
    token_type_ids_padded = padding(token_type_ids, max_length)
    target_ids_padded = token_ids_padded[:, 1:].contiguous()

    return token_ids_padded, token_type_ids_padded, target_ids_padded

