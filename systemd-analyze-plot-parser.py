import sys
import mysql.connector
from svgelements import *


def time_stamp_validation(timeVal):
    """
    Validate and Convert the parse svg Time into seconds

    Parameter
    ----------
    timeVal: string
        Time String parsed from svg

    Returns
    -------
    timeVal: string
        In-place time converted string
    """
    if timeVal[-2:] == "ms":
        timeVal = str(float(timeVal[0:-2]) / 1000)
    elif timeVal[-1:] == "s":
        timeVal = str(float(timeVal[0:-1]))
    return timeVal


def is_float(input_num):
    """
    Checks if an input string is float numeric (i.e) with decimal

    Parameter
    ---------
    input_num: string
        Numeric String input

    Returns
    -------
        Boolean value True or False
    """
    try:
        float(input_num)
        return True
    except ValueError:
        return False


def insert_row(row_list, table_name):
    """
    Insert a parsed row into the table

    Parameters
    ----------
    row_list: string
        String with row values

    table_name: string
        Name of the Table to be inserted
    """
    row_tuple = tuple(row_list)
    insert_query = '''INSERT INTO ''' + table_name + \
        '''(service_name, activation_time, start_time, category) VALUES (%s, NULLIF(%s, "NULL"), %s, %s)'''
    DB_cur.execute(insert_query, row_tuple)
    conn.commit()


def create_table(table_name):
    """
    Create Table for the Build

    Parameter
    --------
    table_name: string
        Build name as a string to be created
    """
    create_TABLE = '''
    CREATE TABLE ''' + table_name + '''(
    id INT PRIMARY KEY AUTO_INCREMENT NOT NULL,
    service_name VARCHAR(255) NOT NULL,
    activation_time DECIMAL(8,4),
    start_time DECIMAL(8,4),
    category VARCHAR(255) NOT NULL
    )'''
    DB_cur.execute(create_TABLE)
    conn.commit()


def parse_SVG(dir_val):
    """
    Parse the svg file into a svg object list

    Parameter
    ---------
    dir_val: string
        directory name that has the systemd-analyze plot SVG
    """
    svg = SVG.parse(dir_val + "/systemdanalyze_plot_" + dir_val + ".svg")
    svg_list.append(svg)


svg_list = []


# SVG Parsing ignore list
svg_ignore_strings = ["Linux", "Startup", "Activating",
                      "Active", "Deactivating", "Setting", "Generators", "Loading"]


# Hard-coded DB Name
dbName = "systemd_analyze_plotter"


# MySQL DB Connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="admin",
)


# Identifier Cursor
DB_cur = conn.cursor()


# Use the DB
use_DB_query = '''USE ''' + dbName
DB_cur.execute(use_DB_query)


# directory list
directories = []  # ["dir1/", "dir2/", "dir3/", ...]
for i in sys.argv:
    if not i in directories:
        if i[-1] == "/":
            directories.append(i[:-1])
        else:
            directories.append(i)
directories.pop(0)  # remove executable from the list


table_list = []
for dir_iter in directories:
    table_list.append(dir_iter)
    # create tables for each dir
    create_table(dir_iter)
    parse_SVG(dir_iter)


list_len = len(svg_list)
big_list = []


for i in range(list_len):
    temp_list = []
    for element in svg_list[i].elements():
        if isinstance(element, SVGText):
            mini_list = []
            first_half = element.text.split()
            if (first_half[0] not in svg_ignore_strings) and (not is_float(first_half[0][:-1])):
                if len(first_half) == 2:
                    # (3.456s)
                    first_half[-1] = time_stamp_validation(
                        first_half[-1][1:-1])
                    mini_list.extend(first_half)
                elif len(first_half) == 3:  # [cec.service, (1min, 16.3s)]
                    seconds_section = float(
                        time_stamp_validation(first_half[-1][:-1]))  # 16.3
                    minutes_section = float(first_half[-2][1:-3]) * 60
                    first_half.pop(-1)
                    first_half[1] = str(minutes_section + seconds_section)
                    mini_list.extend(first_half)
                    pass
                else:
                    mini_list.extend(first_half)
                    mini_list.append("NULL")
            else:
                continue
            mini_list.append(str(element.x/100))
            ext_val = mini_list[0].split(".")[-1]
            if ext_val:
                mini_list.append(ext_val)
            else:
                mini_list.append("default")
            temp_list.append(mini_list)
    big_list.append(temp_list)


count = 0
for image in big_list:
    for row in image:
        insert_row(row, table_list[count])
    count += 1
