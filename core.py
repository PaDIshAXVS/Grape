from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, BigInteger, DateTime, Float
from sqlalchemy.orm import DeclarativeBase, sessionmaker, relationship
from datetime import datetime


sqlite_database = 'sqlite:///Vineyard.db'
engine = create_engine(sqlite_database, echo=True)
Session = sessionmaker(autoflush=True, bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    telegram_id = Column(BigInteger, unique=True)

    vineyard = relationship('Grape', back_populates='user', cascade='all, delete-orphan')
    processing_log = relationship('Obrabotka', back_populates='user', cascade='all, delete-orphan')
    podkormka_log = relationship('Podkormka', back_populates='user', cascade='all, delete-orphan')


    @classmethod
    def load(cls, session, telegram_id):
        user = session.query(cls).filter_by(telegram_id=telegram_id).first()
        if not user:
            user = cls(telegram_id=telegram_id)

            session.add(user)
            session.commit()

        return user
    
    
    def add_grape(self, session, grape):
        self.vineyard.append(grape)

        session.commit()

    def remove_grape(self, session, grape):
        self.vineyard.remove(grape)

        session.commit()


    def add_process(self, session, process):
        self.processing_log.append(process)

        session.commit()

    def remove_process(self, session, process):
        self.processing_log.remove(process)

        session.commit()


    def add_korm(self, session, korm):
        self.podkormka_log.append(korm)

        session.commit()

    def remove_korm(self, session, korm):
        self.podkormka_log.remove(korm)

        session.commit()


class Grape(Base):
    __tablename__ = 'grapes'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    sort = Column(String, default=None)
    location = Column(String, default=None)    
    sort_text = Column(String, default=None)   
    date = Column(DateTime, default=datetime.now)
    briks = Column(Float, default=0.0)
    total = Column(Float, default=0.0)

    user_id = Column(Integer, ForeignKey('users.id'))
    
    user = relationship('User', back_populates='vineyard')
    images = relationship('Image', back_populates='grape', cascade='all, delete-orphan')

    
    @classmethod
    def get_by_user(cls, session, user_id):
        return session.query(cls).filter_by(user_id=user_id).all()


    def add_image(self, session, image):
        self.images.append(image)

        session.commit()


    def remove_image(self, session, image):
        self.images.remove(image)

        session.commit()


class Image(Base):
    __tablename__ = 'images'

    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    file_path = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    grape_id = Column(Integer, ForeignKey('grapes.id'))
    
    grape = relationship('Grape', back_populates='images')


class Obrabotka(Base):
    __tablename__ = 'obrabotka'

    id = Column(Integer, index=True, autoincrement=True, primary_key=True)
    description = Column(String, default=None)
    date = Column(DateTime, default=datetime.now)

    user_id = Column(Integer, ForeignKey('users.id'))

    user = relationship('User', back_populates='processing_log')


class Podkormka(Base):
    __tablename__ = 'podkormka'

    id = Column(Integer, index=True, autoincrement=True, primary_key=True)
    description = Column(String, default=None)
    date = Column(DateTime, default=datetime.now)

    user_id = Column(Integer, ForeignKey('users.id'))

    user = relationship('User', back_populates='podkormka_log')


def setup():
    Base.metadata.create_all(bind=engine)


if __name__ == '__main__':
    setup()