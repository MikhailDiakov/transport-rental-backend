from sqlalchemy import Column, Date, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.base import Base


class CarAvailability(Base):
    __tablename__ = "car_availabilities"

    id = Column(Integer, primary_key=True)
    car_id = Column(Integer, ForeignKey("cars.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    price_per_day = Column(Float, nullable=False)

    car = relationship("Car", back_populates="availabilities")
