from enum import Enum
from sqlalchemy import and_, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from dataclasses import asdict

from uuid import uuid4


# class Registry:
#     def __init__(self, entity_name):
#         self.db = None
#         self.entity = entity_name

#     @staticmethod
#     def trasaction_commit_wrapper(func):
#         def wrapper(self, *args, **kwargs):
#             self.db = self.create_db_session()
#             db_entry = func(self, *args, **kwargs)
#             if isinstance(db_entry, list):
#                 db_entry = [asdict(entry) for entry in db_entry]
#             elif isinstance(db_entry, self.entity):
#                 db_entry = asdict(db_entry)
#             else:
#                 db_entry = {}
#             try:
#                 self.db.commit()
#             except IntegrityError as e:
#                 if "foreign key" in str(e.orig):
#                     raise ValueError()
#                 elif "unique constraint" in str(e.orig):
#                     raise ValueError()
#             finally:
#                 self.db.close()
#             return db_entry

#         return wrapper

#     def create_db_url(self):
#         return f"sqlite:///local.db"

#     def create_db_session(self):
#         db_url = self.create_db_url()
#         engine = create_engine(db_url)
#         SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#         return SessionLocal()

#     @trasaction_commit_wrapper
#     def list_records(self, filters: dict, limit: int, offset: int):
#         filter_values = []
#         for key, value in filters.items():
#             filter_values.append(getattr(self.entity, key) == value)
#         return (
#             self.db.query(self.entity)
#             .filter(and_(*filter_values))
#             .offset(offset)
#             .limit(limit)
#             .all()
#         )

#     @trasaction_commit_wrapper
#     def get_record(self, id: str):
#         res = self.db.query(self.entity).get(id)
#         if not res:
#             raise ValueError("Records not found")
#         return res

#     @trasaction_commit_wrapper
#     def get_record_with_filters(self, filters: dict):
#         filter_values = []
#         for key, value in filters.items():
#             filter_values.append(getattr(self.entity, key) == value)
#         return self.db.query(self.entity).filter(and_(*filter_values)).first()

#     @trasaction_commit_wrapper
#     def create_record(self, data: dict):
#         print(data)
#         self.db.add(data)
#         return data

#     @trasaction_commit_wrapper
#     def update_record(self, id, data: dict):
#         db_entry = self.db.query(self.entity).get(id)
#         if not db_entry:
#             raise ValueError("record not found")
#         for key, value in data.items():
#             setattr(db_entry, key, value)
#         return db_entry

#     @trasaction_commit_wrapper
#     def delete_record(self, id: str):
#         db_entry = self.db.query(self.entity).get(id)
#         if not db_entry:
#             raise ValueError("record not found")
#         self.db.delete(db_entry)


class LocalDB:
    def __init__(self, entity: str):
        self.database = {}
        self.entity = entity

    def list_records(self, filters: dict = {}, limit: int = None, offset: int = None):
        records = []
        if filters:
            for record in self.database.values():
                if any(
                    key not in record or record[key] != value
                    for key, value in filters.items()
                ):
                    continue

                records.append(record)
        else:
            records = list(self.database.values())

        if offset:
            records = records[offset:]
        if limit:
            records = records[:limit]

        return records

    def get_record(self, id: str):
        try:
            return self.database[id]
        except KeyError:
            return False

    def create_record(self, data: dict, p_key: str):
        print(data)
        print(p_key)
        self.database[data[p_key]] = data
        return data

    def update_record(self, id: str, data: dict):
        try:
            self.database[id].update(data)
        except KeyError:
            raise ValueError(self.entity, id)

        return self.database[id]

    def delete_record(self, id: str):
        try:
            del self.database[id]
        except KeyError:
            raise ValueError(self.entity, id)
