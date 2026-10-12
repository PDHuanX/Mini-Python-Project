def chunk_tuple_generator(t, chunk_size=10000):
    """生成器版本，适合处理大数据"""
    for i in range(0, len(t), chunk_size):
        yield t[i:i + chunk_size]