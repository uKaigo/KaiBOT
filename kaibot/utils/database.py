import time
from pymongo import ReturnDocument

# TODO: Implement caching.


class Document:
    __slots__ = ('__collection', '__data')

    def __init__(self, *, data, collection):
        # Don't call our __setattr__
        object.__setattr__(self, '_Document__collection', collection)
        object.__setattr__(self, '_Document__data', data)

    def __iter__(self):
        return iter(self.__data.items())

    def __getattr__(self, attr):
        value = self.__data.get(attr)
        if value:
            return value
        else:
            raise AttributeError(f"'Document' object has no attribute '{attr}'")

    def __setattr__(self, attr, value):
        self.__data[attr] = value

    def update(self, data):
        self.__data.update(data)

    def sync(self):
        return self.__collection.update(self._id, 'set', self.__data)

    def delete(self):
        return self.__collection.delete(self._id)


class CollectionManager:
    __slots__ = ('__collection', 'template')

    def __init__(self, *, collection, template=None):
        if template is None:
            template = {}
        self.__collection = collection
        self.template = template

    async def new(self, id):
        template = self.template.copy()
        template.update({'_id': str(id)})

        return await self.__collection.insert_one(template)

    async def delete(self, id):
        id = str(id)

        await self.collection.delete_one({'_id': id})

    async def find(self, id):
        id = str(id)

        return await self.collection.find_one({'_id': id})

    async def update(self, id, operation, data):
        id = str(id)

        return await self.__collection.find_one_and_update(
            {'_id': id}, {f'${operation}': data}, return_document=ReturnDocument.AFTER
        )

    async def delete(self, id):
        id = str(id)
        await self.__collection.delete({'_id': id})

    async def all(self):
        cursor = self.collection.find({})
        async for doc in cursor:
            yield doc

    async def ping(self):
        start = time.perf_counter()
        await self.__collection.find_one({})
        return time.perf_counter() - start


class DatabaseManager:
    __slots__ = ('__db',)

    def __init__(self, name, *, client):
        self.__db = client[name]

    def get_collection(self, name, template=None):
        return CollectionManager(collection=self.__db[name], template=template)
