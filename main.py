import sqlite3
import numpy as np
import math
import matplotlib.pyplot as plt


##################################################################
#
# print_stats
#
# Given a connection to the CTA database, executes various
# SQL queries to retrieve and output basic stats.
#
def print_stats(dbConn):
    dbCursor = dbConn.cursor()

    print("General Statistics:")
    db_conn = sqlite3.connect("/Users/andreais_745/Documents/GitHub/CTA_Ridership/CTA2_L_daily_ridership.db")
    dbCursor = db_conn.cursor()
    # NUM OF STATIONS
    dbCursor.execute("Select count(*) From Stations;")
    row = dbCursor.fetchone();
    print("  # of stations:", f"{row[0]:,}")
    #NUM OF STOPS
    dbCursor.execute("Select count(*) From Stops;")
    row = dbCursor.fetchone();
    print("  # of stops:", f"{row[0]:,}")
    #NUM OF RIDE ENTRIES
    dbCursor.execute("Select count(*) From Ridership;")
    row = dbCursor.fetchone();
    print("  # of ride entries:", f"{row[0]:,}")
    #DATE RANGE
    dbCursor.execute(
        " Select Substring ((min(Ride_Date)), 0, 11), Substring ((max(Ride_Date)), 0, 11) from Ridership ; ")
    row = dbCursor.fetchone();
    print("  date range:", row[0], "-", row[1])
    #TOTAL RIDERSHIP
    dbCursor.execute("select sum(Num_Riders) from Ridership; ")
    total = dbCursor.fetchone();
    print("  Total ridership:", f"{total[0]:,}")

    dbCursor.close()


##################################################################
# Function 1 -> Finding Stations with Extact Case or Partial Name (e.g %uic% -> UIC-Halsted),
# Printing Them Out in Ascending Order
def func_1(dbConn):
    dbCursor = dbConn.cursor()
    print()
    inputf1 = input("Enter partial station name (wildcards _ and %): ")
    # query using Stations data
    sql1 = """ Select Station_Id, Station_Name 
  from Stations
  where Station_Name like ?
  order by Station_Name asc;"""
    dbCursor.execute(sql1, [inputf1])

    answerOne = dbCursor.fetchall()
    # no stations found
    if len(answerOne) == 0:
        print("**No stations found...")
        return None
    # printing out row by row
    for row in answerOne:
        print(row[0], ":", row[1])
    dbCursor.close()


##################################################################
# Function Two calls for finding the ridership data corresponding to the day of the week and holidays using user input
#
def func_2(dbConn):
    dbCursor = dbConn.cursor()
    print()
    # Get the station name from the user
    station_name = input("Enter the name of the station you would like to analyze: ")

    # Query uses ridership and joined with stations to find the total amount for the user input station
    total_ridership_query = """SELECT sum(Num_Riders)
                                   FROM Ridership
                                   JOIN Stations ON Ridership.Station_ID = Stations.Station_ID
                                   WHERE Stations.Station_Name = ?"""
    dbCursor.execute(total_ridership_query, [station_name])
    total_result = dbCursor.fetchone()

    if not total_result or total_result[0] is None:
        print("**No data found...")
        return None

    total_ridership = total_result[0]

    # Query uses Ridership and Stations data to get the ridership for weekdays, Saturdays, and Sundays/holidays for the specified station
    ridership_query = """SELECT sum(CASE WHEN Type_of_Day = 'W' THEN Num_Riders ELSE 0 END) as Weekday,
                                       sum(CASE WHEN Type_of_Day = 'A' THEN Num_Riders ELSE 0 END) as Saturday,
                                       sum(CASE WHEN Type_of_Day = 'U' THEN Num_Riders ELSE 0 END) as SundayHoliday
                            FROM Ridership
                            JOIN Stations ON Ridership.Station_ID = Stations.Station_ID
                            WHERE Stations.Station_Name = ?"""
    dbCursor.execute(ridership_query, [station_name])
    ridership_result = dbCursor.fetchone()

    if not ridership_result or ridership_result[0] is None:
        print("**No data found...")
        return None
    # Gatering data into their respected box
    weekday_riders, saturday_riders, sunday_holiday_riders = ridership_result
    # Display
    print(f"Percentage of ridership for the {station_name} station: ")
    print("  Weekday ridership:", f"{weekday_riders:,}", f"({(weekday_riders / total_ridership) * 100.0:.2f}%)")
    print("  Saturday ridership:", f"{saturday_riders:,}", f"({(saturday_riders / total_ridership) * 100.0:.2f}%)")
    print("  Sunday/holiday ridership:", f"{sunday_holiday_riders:,}", f"({(sunday_holiday_riders / total_ridership) * 100.0:.2f}%)")
    print(f"  Total ridership:", f"{total_ridership:,}")

    dbCursor.close()


###################################################################
# Output the total ridership on weekdays for each station using station names
def func_3(dbConn):
    dbCursor = dbConn.cursor()
    print("Ridership on Weekdays for Each Station")
    # finding the total sum to calculate percentage later on
    dbCursor.execute("select sum(CASE WHEN Type_of_Day = 'W' THEN Num_Riders ELSE 0 END) as Weekday from Ridership; ")
    total = dbCursor.fetchone();
    # finding the sum of weekday riders for a specified station_name
    sql3 = """  SELECT Stations.Station_Name ,sum(CASE WHEN Type_of_Day = 'W' THEN Num_Riders ELSE 0 END) as Weekday
   FROM Ridership JOIN Stations
   ON Ridership.Station_ID = Stations.Station_ID
  GROUP BY Station_Name
   order by Weekday desc"""
    dbCursor.execute(sql3)
    answ3 = dbCursor.fetchall()
    # calculating the percentage was easier to calculate in the print statement than printing it in function two
    for row in answ3:
        print(row[0], ":", f"{row[1]:,}", f'({row[1] / total[0] * 100:.2f}%)')
    dbCursor.close()
##################################################################
#Given a line color and direction, output all the stops for that line color in that direction.
#Order by stop name in ascending order
def func_4(dbConn):
    dbCursor = dbConn.cursor()
    print()
    #ask for line color
    input_color = input(
        "Enter a line color (e.g. Red or Yellow): ").upper()  # Convert to lowercase for case-insensitivity

    # Check if the line color exists
    color_check_query = "SELECT Line_ID FROM Lines WHERE Color LIKE ?"
    dbCursor.execute(color_check_query, [input_color])
    color_result = dbCursor.fetchone()

    if not color_result or color_result[0] is None:
        print("**No such line...")
        dbCursor.close()
        return None
    #Ask for line direction
    input_direction = input("Enter a direction (N/S/W/E): ").upper()  # Convert to lowercase for case-insensitivity
    # Line color exists, now check if the line runs in the chosen direction using Stops and Lines data
    direction_check_query = """SELECT Stops.Stop_Name, Stops.ADA
                               FROM Stops
                               JOIN StopDetails ON Stops.Stop_ID = StopDetails.Stop_ID
                               JOIN Lines ON StopDetails.Line_ID = Lines.Line_ID
                               WHERE Lines.Color LIKE ? AND Stops.Direction LIKE ?
                               ORDER BY Stops.Stop_Name ASC"""
    #input_color - user color
    #input_direction - user direction
    dbCursor.execute(direction_check_query, [input_color, input_direction])
    stops_result = dbCursor.fetchall()

    if len(stops_result) == 0:
        print("**That line does not run in the direction chosen...")
    # print out the stations if the line runs in the direction
    else:
        for row in stops_result:
            if row[1] == 1:
                print(f"{row[0]} : direction = {input_direction} (handicap accessible)")
            else:
                print(f"{row[0]} : direction = {input_direction} (not handicap accessible)")

    dbCursor.close()
##################################################################
#Output the number of stops for each line color, separated by direction.
def func_5(dbConn):
    dbCursor = dbConn.cursor()

    # SQL query to get the total number of stops
    total_stops_query = "SELECT COUNT(*) FROM Stops;"
    dbCursor.execute(total_stops_query)
    total_stops_result = dbCursor.fetchone()
    total_stops = total_stops_result[0]

    # SQL query to get the number of stops for each line color and direction using Stops,stopDetails, and Lines
    stops_query = """SELECT Lines.Color, Stops.Direction, COUNT(*) as StopsCount
                 FROM Stops
                 JOIN StopDetails ON Stops.Stop_ID = StopDetails.Stop_ID
                 JOIN Lines ON StopDetails.Line_ID = Lines.Line_ID
                 GROUP BY Lines.Color, Stops.Direction
                 ORDER BY Lines.Color ASC, Stops.Direction ASC;"""

    dbCursor.execute(stops_query)
    stops_result = dbCursor.fetchall()
    print("Number of Stops For Each Color By Direction")
    for row in stops_result:
        #varaible to its own row
        color, direction, stops_count = row
        # finding the percentage
        percentage = (stops_count / total_stops) * 100
        print(f"{color:1} going {direction:1} : {stops_count:1,} ({percentage:.2f}%)")

    dbCursor.close()
##################################################################
#Given a station name, output the total ridership for each year for that station, in
#ascending order by year
def func_6(dbConn):
    dbCursor = dbConn.cursor()

    # Get stop name from user input with wildcards
    input_stop = input("\nEnter a station name (wildcards _ and %): ")

    # SQL query to find stop(s) based on user input
    stop_query = """SELECT Station_Name
                        FROM Stations
                        WHERE Station_Name LIKE ?;"""

    dbCursor.execute(stop_query, [input_stop])
    stops = dbCursor.fetchall()
    # return none where no stations are found or mutiple stations are found
    if len(stops) == 0:
        print("**No station found...")
        return None

    elif len(stops) > 1:
        print("**Multiple stations found...")
        return None
    else:
        # getting the names and id
        stationSixName = stops[0][0]

        # SQL query to get yearly ridership data for the specified stop
        yearly_data_query = """SELECT strftime('%Y', Ride_Date) as Year, sum(Num_Riders) as TotalRiders
                                   FROM Ridership
                                   JOIN Stations ON Ridership.Station_ID = Stations.Station_ID
                                   WHERE Stations.Station_Name LIKE ?
                                   GROUP BY Year
                                   ORDER BY Year ASC;"""

        dbCursor.execute(yearly_data_query, [input_stop])
        yearly_data = dbCursor.fetchall()

        # Display the yearly ridership data
        print(f"Yearly Ridership at {stationSixName}")
        print()
        for row in yearly_data:
            print(f"{row[0]} : {row[1]:,}")

        # Ask user if they want to plot the data
        plot_option = input("\nPlot? (y/n) ")

        if plot_option.lower() == 'y':
            x = []  # create 2 empty vectors/lists
            y = []
            # getting the years from data
            labels = [str(row[0]) for row in yearly_data]
            #counter
            year = 1

            for row in yearly_data:  # append each (x, y) coordinate to plot x.append
                x.append(year)
                #num of riders
                y.append(row[1])
                year += 1

            plt.xlabel("Year")
            plt.ylabel("Number of Riders")
            plt.title(f"Yearly Ridership at {stationSixName}")
            plt.plot(x, y)
            plt.xticks(x, labels, fontsize=6)
            plt.tight_layout()
            plt.show(block=False)
##################################################################
#Given a station name and year, output the total ridership for each month in that year.
def func_7(dbConn):
    dbCursor = dbConn.cursor()
    print()
    station = input("Enter a station name (wildcards _ and %): ")
    station_query = """SELECT Station_Name
                        FROM Stations
                        WHERE Station_Name LIKE ?;"""

    dbCursor.execute(station_query, [station])
    stations = dbCursor.fetchall()

    if len(stations) == 0:
        print("**No station found...")
        return None
    elif len(stations) > 1:
        print("**Multiple stations found...")
        return None
    else:
        # Extract the station name without parentheses and quotes
        station_name = stations[0][0]

        year = input("Enter a year: ")
        sql7 = """SELECT strftime('%m/%Y', Ride_Date) as Month, sum(Num_Riders) FROM Ridership 
                  JOIN Stations ON Ridership.Station_ID = Stations.Station_ID 
                  WHERE Stations.Station_Name LIKE ? AND strftime('%Y', Ride_Date) = ?
                  GROUP BY Month
                  ORDER BY Month ASC"""

        dbCursor.execute(sql7, [station, year])
        monthly_data = dbCursor.fetchall()

        print(f"Monthly Ridership at {station_name} for {year}")
        print()
        for row in monthly_data:
            print(f"{row[0]} : {row[1]:,}")
        print()
        # Ask user if they want to plot the data
        plot_option = input("Plot? (y/n) ")

        if plot_option.lower() == 'y':
            # Extract month and year separately
            months = [int(row[0].split('/')[0]) for row in monthly_data]

            # Plot the data
            plt.figure(figsize=(10, 6))
            plt.plot(months, [row[1] for row in monthly_data]) # months and number of riders
            plt.xlabel("Month")
            plt.ylabel("Number of Riders")
            plt.title(f"Monthly Ridership at {station_name} Station for {year}")
            plt.xticks(range(1, 13), [str(i) for i in range(1, 13)]) # plot the 12 months
            plt.show()
##################################################################
#Given two station names and year, output the total ridership for each day in that year.
def func_8(dbConn):
    dbCursor = dbConn.cursor()
    print()

    input1 = input("Year to compare against? ")
    print()
    # STATION ONE
    input2 = input("Enter station 1 (wildcards _ and %): ")
    station_sql = """SELECT Station_ID, Station_Name FROM Stations WHERE Station_Name LIKE ?"""
    dbCursor.execute(station_sql, (input2,))
    stationOne = dbCursor.fetchall()
    # if fetched data is 0 or more than one return none
    if len(stationOne) == 0:
        print("**No station found...")
        dbCursor.close()
        return None
    elif len(stationOne) > 1:
        print("**Multiple stations found...")
        dbCursor.close()
        return None
    else:
        stationOne = stationOne[0]

    print()
    #STATION TWO
    input3 = input("Enter station 2 (wildcards _ and %): ")
    dbCursor.execute(station_sql, (input3,))
    stationTwo = dbCursor.fetchall()
    # if fetched data is 0 or more than one return none
    if len(stationTwo) == 0:
        print("**No station found...")
        dbCursor.close()
        return
    elif len(stationTwo) > 1:
        print("**Multiple stations found...")
        dbCursor.close()
        return
    else:
        stationTwo = stationTwo[0]

        sql1 = """SELECT date(Ride_Date) as date, SUM(Num_Riders) as sum
                  FROM Ridership 
                  WHERE strftime('%Y', Ride_Date) LIKE ? AND Station_ID LIKE ?
                  GROUP BY date(Ride_Date)
                  ORDER BY date(Ride_Date) ASC"""

        dbCursor.execute(sql1, [input1, stationOne[0]])
        answ1 = dbCursor.fetchall()
        #Displaying Station One
        print(f"Station 1: {stationOne[0]} {stationOne[1]}")
        for row in answ1[:5] + answ1[-5:]:
            print(row[0], row[1])

        dbCursor.execute(sql1, [input1, stationTwo[0]])
        answ2 = dbCursor.fetchall()
        # Displaying Station Two
        print(f"Station 2: {stationTwo[0]} {stationTwo[1]}")
        for row in answ2[:5] + answ2[-5:]:
            print(row[0], row[1])

        print()

        inputPlot = input("Plot? (y/n) ")
        if inputPlot.lower() == 'y':
            x = np.arange(1, len(answ1) + 1)
            x2 = np.arange(1, len(answ2) + 1)

            y = [row[1] for row in answ1]
            y2 = [row[1] for row in answ2]

            plt.xlabel("Day")
            plt.ylabel("Number of Riders")
            message = f"Riders Each Day of {input1}"
            plt.title(message)
            plt.plot(x, y, label=f"{stationOne[1]}")
            plt.plot(x2, y2, label=f"{stationTwo[1]}")
            plt.legend(loc='upper right')
            plt.show(block=False)
##################################################################
#Given a set of latitude and longitude from the user, find all stations within a mile square radius.
def func_9(dbConn):
    dbCursor = dbConn.cursor()
    print()
    #LATITUDE
    input_lat = float(input("Enter a latitude: "))
    # CHECK IF LATITUDE AND LONGITUDE IS OUT OF BOUNDS
    if not (40 <= input_lat <= 43):
        print(
            "**Latitude entered is out of bounds...")
        return None
    input_lon = float(input("Enter a longitude: "))
    if not (-88 <= input_lon <= -87):
        print("**Longitude entered is out of bounds...")
        return None
    #CALCULATE MILE
    mile_radius_lat = 1 / 69
    mile_radius_lon = 1 / 51
    latUpper = round(input_lat + mile_radius_lat, 3)
    latLower = round(input_lat - mile_radius_lat, 3)
    longUpper = round(input_lon + mile_radius_lon, 3)
    longLower = round(input_lon - mile_radius_lon, 3)
    #FIND STATIONS WITHIN MILE USING STOPS AND STATIONS
    sql = """SELECT Distinct (Stations.Station_Name), Stops.Longitude, Stops.Latitude
             FROM Stations 
             JOIN Stops ON Stations.Station_ID = Stops.Station_ID
             WHERE Stops.Latitude BETWEEN ? AND ?
               AND Stops.Longitude BETWEEN ? AND ?
             ORDER BY Stations.Station_Name ASC"""

    dbCursor.execute(sql, (latLower, latUpper, longLower, longUpper))

    answ = dbCursor.fetchall()
    #RETURN NONE IF NO STATIONS ARE FOUND
    if len(answ) == 0:
        print("**No stations found...")
        dbCursor.close()
        return None
    print()
    #DISPLAY RESULTS
    print("List of Stations Within a Mile")
    for row in answ:
        # CUTTING OFF THE LATITIUDE AND LONGITUDE REACHES ZERO IN DECIMAL
        latitude_str = "{:.10f}".format(row[2]).rstrip('0').rstrip('.')
        longitude_str = "{:.10f}".format(row[1]).rstrip('0').rstrip('.')
        print(f"{row[0]} : ({latitude_str}, {longitude_str})")

    print()
    input_plot = input("Plot? (y/n) ")

    if input_plot.lower() == 'y':
        x = []
        y = []

        for row in answ:
            x.append(row[1])
            y.append(row[2])

        image = plt.imread("chicago.png")
        xydims = [-87.9277, -87.5569, 41.7012, 42.0868]
        plt.imshow(image, extent=xydims)
        plt.title("Stations within 1-mile radius")
        plt.plot(x, y, "o", c="blue")
        #PLOT
        for row in answ:
            plt.annotate(row[0], (row[1], row[2]))
        #LIMIT
        plt.xlim([-87.9277, -87.5569])
        plt.ylim([41.7012, 42.0868])
        plt.show(block=False)

##################################################################
print('** Welcome to CTA L analysis app **')
print()

dbConn = sqlite3.connect("/Users/andreais_745/Documents/GitHub/CTA_Ridership/CTA2_L_daily_ridership.db")

print_stats(dbConn)

while True:
    print()
    print("Please enter a command (1-9, x to exit): ", end='')
    input1 = input()
    if input1 == "1":
        func_1(dbConn)
    elif input1 == "2":
        func_2(dbConn)
    elif input1 == "3":
        func_3(dbConn)
    elif input1 == "4":
        func_4(dbConn)
    elif input1 == "5":
        func_5(dbConn)
    elif input1 == "6":
        func_6(dbConn)
    elif input1 == "7":
        func_7(dbConn)
    elif input1 == "8":
        func_8(dbConn)
    elif input1 == "9":
        func_9(dbConn)
    elif input1 == "x":
        break
    else:
        print("**Error, unknown command, try again...")

dbConn.close()
#
# done
#