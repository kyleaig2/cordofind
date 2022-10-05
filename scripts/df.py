import pandas as pd


def _func(x, y): 
    if y in x.split(','):
        return x
    elif (x and y):
        return x + ',' + y
    else: 
        return x or y

def consolidate(a: pd.DataFrame, b: pd.DataFrame):
    if a.empty: return b
    if b.empty: return a

    df = a.combine_first(b).merge(b['Connection'], how='outer', on='Handle').fillna('')
    x = df['Connection_x']
    y = df['Connection_y']
    
    df['Connection'] = x.combine(y, func=_func, fill_value='')
    df =  df.drop(['Connection_x', 'Connection_y'], axis=1)

    return df

# test

# men_csv = './csvs/menitrust/menitrust_followers.csv'
# home_csv = './csvs/hoomeshaake/hoomeshaake_followers.csv'

# menitrust = pd.read_csv(men_csv, index_col='Handle')
# homeshake = pd.read_csv(home_csv, index_col='Handle')

# merged = consolidate(menitrust, homeshake)
# print(merged)

# merged.to_csv('./csvs/merged.csv')
