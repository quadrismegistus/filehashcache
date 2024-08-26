from . import *

def is_jsonable(obj):
    return isinstance(obj, (dict, list, str, int, float, bool, type(None)))


def prune_none_values(data, badkeys=None):
    if isinstance(data, dict):
        return {k: prune_none_values(v) for k, v in data.items() if v is not None and (not badkeys or k not in badkeys)}
    elif isinstance(data, list):
        return [prune_none_values(item) for item in data if item is not None]
    else:
        return data

# @log.debug
def is_dir(path):
    fn, ext = os.path.splitext(path)
    return not bool(ext)

# @log.debug
def ensure_dir(path):
    if not is_dir(path): 
        path=os.path.dirname(path)
    return os.makedirs(path, exist_ok=True)

def reset_index_misc(df, _index=False):
    import pandas as pd
    index = [x for x in df.index.names if x is not None]
    df = df.reset_index() if index else (df if not _index else df.rename_axis('_index').reset_index())
    return df, (index if index or not _index else ['_index'])


def get_fn_ext(fn):
    # without period
    return fn.split('.')[-1]

class ReusableGenerator:
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __iter__(self):
        return self.func(*self.args, **self.kwargs)

def rmtreefn(dir_path):
    if not os.path.exists(dir_path): return
    try:
        if os.path.isdir(dir_path):
            shutil.rmtree(dir_path, ignore_errors=True)
            # log.info(f'Deleted temporary directory: {dir_path}')
        elif os.path.isfile(dir_path):
            os.remove(dir_path)
            # log.info(f'Deleted temporary file: {dir_path}')
        else:
            log.warning(f'Temporary path does not exist: {dir_path}')
    except Exception as e:
        log.debug(f'Failed to delete temporary path {dir_path}: {e}')

def get_encoding_str(compress,b64):
    return "+".join(filter(None, [
        "zlib" if compress else None,
        "b64" if b64 else None
    ]))

def is_method(func):
    """
    Check if a function object is a method by inspecting its first parameter.
    
    :param func: The function object to check
    :return: True if the function is likely a method, False otherwise
    """
    params = inspect.signature(func).parameters
    return len(params) > 0 and list(params.keys())[0] == 'self'
def fast_concat(*dfs):
    import pandas as pd
    
    # # Reset index for all DataFrames before concatenation
    # reset_dfs = [df.reset_index(drop=True) for df in dfs]
    
    # Concatenate the reset DataFrames
    result = pd.concat(list(dfs), axis=0, ignore_index=True, join='outer')
    
    return result
def slow_concat(*dfs):
    import pandas as pd
    return pd.DataFrame([
        d
        for df in dfs
        for d in df.to_dict(orient='records')
    ])

def is_nan(x):
    import numpy as np
    try:
        return np.isnan(x)
    except Exception:
        return False
    
def _flatten_ld(item, ind=None):
    if ind is None:
        ind = {}

    if isinstance(item, dict):
        item_d = {}
        item_ld = [item_d]
        for k, v in item.items():
            if isinstance(v, (dict, list)) or is_dataframe(v):
                new_ld = [
                    {
                        k2 if k2[0] == "_" or k[0]=='_' else f"{k}.{k2}": v2
                        for k2, v2 in d.items()
                    }
                    for d in _flatten_ld(v, ind)
                ]
                item_ld.extend(new_ld)
            else:
                item_d[k] = v
        return [{**ind, **v} for v in item_ld]
    elif is_dataframe(item):
        return [
            {**ind, **row.to_dict()}
            for _, row in reset_index_misc(item, _index=False)[0].iterrows()
        ]
    elif isinstance(item, list):
        return [
            row for subitem in item for row in _flatten_ld(subitem, ind)
        ]
    else:
        return [{**ind, "_value": item}]
    

def flatten_ld(item, ind={}):
    if isinstance(item, (dict, list)) or is_dataframe(item):
        return [d for d in _flatten_ld(item,ind) if isinstance(d,dict) and d]
    else:
        return [{**ind, "_value": item}]

def is_meta_col(col):
    return col and col[0]=='_' and col not in {'_key','_value'}

def filter_ld(ld, no_nan=False, no_meta=False):
    ld = [
        {k: v for k, v in d.items() if (not no_nan or not is_nan(v)) and (not no_meta or not is_meta_col(k))}
        for d in ld
    ]
    ld = [d for d in ld if isinstance(d,dict) and len(d) and (not '_key' in ld or len(d)>1)]
    return ld


def filter_df(df, with_metadata=False, index=True, index_cols=None, key_col='_key', value_col='_value'):
    if not with_metadata:
        df = df[[c for c in df.columns if c[0]!='_' or c in {key_col,value_col}]]
    if index:
        if not index_cols:
            index_cols = [x for x in df if x[0] == "_" and x!=value_col]
        if index_cols:
            df = df.set_index(index_cols if index_cols else prefix_cols)
    prefix_cols = [x for x in df if x[0] == "_"]
    non_prefix_cols = [x for x in df if x[0] != "_"]
    df = df[prefix_cols + non_prefix_cols]
    return df

def separate_index(df, _index=None):
    index = [x for x in df.index.names if x is not None]
    return (df if not index else df.reset_index()),index

def is_dataframe(df):
    return get_obj_addr(df).endswith("DataFrame")

