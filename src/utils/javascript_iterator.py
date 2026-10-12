def public_java_style_iterator(collection):
    return JavaStyleIterator(collection)

class JavaStyleIterator:
    def __init__(self, collection):
        self.collection = collection
        self.current_index = 0
        self.last_index = -1  # 记录最后一次访问的索引，用于 remove 操作
        self.allow_remove = False

    def has_next(self):
        """检查是否还有下一个元素"""
        return self.current_index < len(self.collection)

    def next(self):
        """获取下一个元素"""
        if not self.has_next():
            raise StopIteration("没有更多元素")

        self.allow_remove = True
        self.last_index = self.current_index
        value = self.collection[self.current_index]
        self.current_index += 1
        return value

    def remove(self):
        """删除最后一次通过 next() 返回的元素"""
        if not self.allow_remove:
            raise RuntimeError("在调用 remove() 之前必须先调用 next()")

        if self.last_index < 0:
            raise RuntimeError("没有元素可以删除")

        # 删除元素并调整索引
        del self.collection[self.last_index]
        self.current_index -= 1  # 因为删除了一个元素，索引要回退
        self.allow_remove = False  # 一次 remove 后需要再次调用 next() 才能 remove