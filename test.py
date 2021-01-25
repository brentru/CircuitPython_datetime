from adafruit_datetime import timedelta

# Example of normalization
year = timedelta(days=365)
another_year = timedelta(weeks=40, days=84, hours=23,
                         minutes=50, seconds=600)
print(year == another_year)
print("Total seconds in the year: ", year.total_seconds())

# Example of timedelta arithmetic
year = timedelta(days=365)
ten_years = 10 * year
print(ten_years)

print(ten_years.days // 365)

nine_years = ten_years - year
print(nine_years)

three_years = nine_years // 3
print(three_years, three_years.days // 365)