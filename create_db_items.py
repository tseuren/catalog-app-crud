#!/usr/bin/env python2.7

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_setup import Category, Base, Item, User

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

user1 = User(id=0, name='test',
             email='test@test.com',
             picture='https://image.flaticon.com/icons/svg/270/270137.svg')
session.add(user1)
session.commit()

category1 = Category(name="Soccer")
session.add(category1)
session.commit()

category2 = Category(name="Basketball")
session.add(category2)
session.commit()

category3 = Category(name="Frisbee")
session.add(category3)
session.commit()

category4 = Category(name="Snowboarding")
session.add(category4)
session.commit()

category5 = Category(name="Skating")
session.add(category5)
session.commit()

menuItem1 = Item(name="Soccer Ball", description="A soccer ball, duh.",
                 category=category1, user_id=0, filename=None)
session.add(menuItem1)
session.commit()
menuItem2 = Item(name="Socks", description="Very comfy.",
                 category=category1, user_id=0, filename=None)
session.add(menuItem2)
session.commit()
menuItem3 = Item(name="Shinguards", description="Protect your shins.",
                 category=category1, user_id=0, filename=None)
session.add(menuItem3)
session.commit()
menuItem4 = Item(name="Basket Ball", description="A basket ball, duh.",
                 category=category2, user_id=0, filename=None)
session.add(menuItem4)
session.commit()
menuItem5 = Item(name="Basket",
                 description="Try throwing the ball into the basket, great "
                 "fun wow yea.", category=category2, user_id=0,
                 filename=None)
session.add(menuItem5)
session.commit()
menuItem6 = Item(name="Frisbee", description="A frisbee, you can throw it.",
                 category=category3, user_id=0, filename=None)
session.add(menuItem6)
session.commit()
menuItem7 = Item(name="Even more frisbees!", description="...",
                 category=category3, user_id=0, filename=None)
session.add(menuItem7)
session.commit()
menuItem8 = Item(name="Yay, frisbees!", description="sigh",
                 category=category3, user_id=0, filename=None)
session.add(menuItem8)
session.commit()
menuItem9 = Item(name="Snowboard", description="(Snow not included)",
                 category=category4, user_id=0, filename=None)
session.add(menuItem9)
session.commit()
menuItem10 = Item(name="Snow", description="hheh.", category=category4,
                  user_id=0, filename=None)
session.add(menuItem10)
session.commit()
menuItem11 = Item(name="Goggles", description="Never be snowblind again!",
                  category=category4, user_id=0, filename=None)
session.add(menuItem11)
session.commit()
menuItem12 = Item(name="Skateboard", description="R A D I C A L",
                  category=category5, user_id=0, filename=None)
session.add(menuItem12)
session.commit()
menuItem13 = Item(name="Bearings", description="Make those wheels spin.",
                  category=category5, user_id=0, filename=None)
session.add(menuItem13)
session.commit()
menuItem14 = Item(name="Skateboard Toolkit",
                  description="All you need to fix up your board, maybe.",
                  category=category5, user_id=0, filename=None)
session.add(menuItem14)
session.commit()
