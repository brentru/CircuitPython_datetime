# Example of working with a `timedelta` object
from adafruit_datetime import timedelta

# Example of normalization
year = timedelta(days=365)
another_year = timedelta(weeks=40, days=84, hours=23,
                         minutes=50, seconds=600)
print("Total seconds in the year: ", year.total_seconds())

# Example of timedelta arithmetic
year = timedelta(days=365)
ten_years = 10 * year
print('Days in ten years:', ten_years)

nine_years = ten_years - year
print('Days in nine years:', nine_years)

three_years = nine_years // 3
print('Days in three years:', three_years, three_years.days // 365)