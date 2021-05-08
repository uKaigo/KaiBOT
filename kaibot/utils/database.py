import time
from collections import deque

from pymongo import ReturnDocument


class _missing:
    obj = object()


MISSING = _missing()


class Document:
    __slots__ = ('__collection', '__data')

    def __init__(self, data, collection):
        # Don't call our __setattr__
        object.__setattr__(self, '_Document__collection', collection)
        object.__setattr__(self, '_Document__data', data)

    def __iter__(self):
        return iter(self.__data.items())

    def __getattr__(self, attr):
        value = self.__data.get(attr, MISSING)
        if value is not MISSING:
            return value
        super().__getattr__(attr)

    def __setattr__(self, attr, value):
        self.__data[attr] = value

    def update(self, data):
        self.__data.update(data)

    def sync(self):
        return self.__collection.update(self._id, 'set', self.__data)

    def delete(self):
        return self.__collection.delete(self._id)


class LRUCache:
    def __init__(self, max_size=None):
        self.max_size = max_size
        self.__container = deque()
        self.__map = dict()

    def _reallocate(self):
        self.__map = dict()
        if len(self.__container) > 0:
            for key, value in enumerate(self.__container):
                self.__map[value[0]] = key

    def get(self, key):
        if key in self.__map:
            value = self.__container[self.__map[key]]
            self.__container.remove(value)
            self.__container.appendleft(value)
            self._reallocate()

            return value[1]

        return MISSING

    def insert(self, key, value):
        if key in self.__map:
            index = self.__map[key]
            self.__container[index] = (key, value)
        else:
            if len(self.__container) == self.max_size:
                self.__container.pop()
            self.__container.appendleft((key, value))

        self._reallocate()

        return value

    def delete(self, key):
        if key in self.__map:
            self.__container[self.__map[key]].remove()
            self._reallocate()


class CollectionManager:
    __slots__ = ('__collection', '__cache', 'template')

    def __init__(self, *, collection, template=None):
        if template is None:
            template = {}
        self.__cache = LRUCache(500)
        self.__collection = collection
        self.template = template

    async def new(self, id):
        template = self.template.copy()
        template.update({'_id': str(id)})

        data = await self.__collection.insert_one(template)
        return self.__cache.insert(id, Document(data, self))

    async def delete(self, id):
        id = str(id)

        await self.__collection.delete_one({'_id': id})
        self.__cache.delete(id)

    async def find(self, id):
        id = str(id)

        cached = self.__cache.get(id)
        if cached is not MISSING:
            return cached

        data = await self.__collection.find_one({'_id': id})
        if not data:
            return self.__cache.insert(id, None)
        return self.__cache.insert(id, Document(data, self))

    async def update(self, id, operation, data):
        id = str(id)

        data = await self.__collection.find_one_and_update(
            {'_id': id}, {f'${operation}': data}, return_document=ReturnDocument.AFTER
        )
        return self.__cache.insert(id, Document(data, self))

    async def all(self):
        cursor = self.__collection.find({})
        async for doc in cursor:
            yield Document(doc, self)

    async def ping(self):
        start = time.perf_counter()
        await self.__collection.find_one({})
        return time.perf_counter() - start


class DatabaseManager:
    __slots__ = ('__db', '__cache')

    def __init__(self, name, *, client):
        self.__cache = {}
        self.__db = client[name]

    def create_collection(self, name, template=None):
        col = CollectionManager(collection=self.__db[name], template=template)
        self.__cache[name.casefold()] = col
        return col

    def __getattr__(self, attr):
        if attr.casefold() in self.__cache:
            return self.__cache[attr.casefold()]
        super().__getattr__(attr)
