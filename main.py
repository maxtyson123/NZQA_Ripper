from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import os
import sys

import requests
from bs4 import BeautifulSoup

YEARS = [2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]
ANSWER_URL = "https://www.nzqa.govt.nz/nqfdocs/ncea-resource/schedules/"
ASSESSMENT_URL = "https://www.nzqa.govt.nz/nqfdocs/ncea-resource/exams/"
EXEMPLAR_URL = "https://www.nzqa.govt.nz/nqfdocs/ncea-resource/exemplars/"

class Driver:
    name = ""
    answer_url = ""
    assessment_url = ""
    exemplar_url = ""

    def __init__(self, name, answer_url, assessment_url, exemplar_url):
        self.name = name
        self.answer_url = answer_url
        self.assessment_url = assessment_url
        self.exemplar_url = exemplar_url

    def get_answer_url(self, standard, year):
        return self.answer_url

    def get_assessment_url(self, standard, year):
        return self.assessment_url

    def get_exemplar_url(self, standard, year, exam_type):
        return self.exemplar_url


class NZQA(Driver):
    def __init__(self):
        super().__init__("NZQA", "https://www.nzqa.govt.nz/nqfdocs/ncea-resource/schedules/", "https://www.nzqa.govt.nz/nqfdocs/ncea-resource/exams/", "https://www.nzqa.govt.nz/nqfdocs/ncea-resource/exemplars/")

    def get_answer_url(self, standard, year):
        return f"{self.answer_url}/{year}/{standard}-ass-{year}.pdf"

    def get_assessment_url(self, standard, year):
        return f"{self.assessment_url}/{year}/{standard}-exm-{year}.pdf"

    def get_exemplar_url(self, standard, year, exam_type):
        return f"{self.exemplar_url}/{year}/{standard}-exp-{year}-{exam_type}.pdf"


class StudyTime(Driver):

    def __init__(self):
        super().__init__("StudyTime", "https://studytime.co.nz/wp-content/uploads/2024/06/", "https://studytime.co.nz/wp-content/uploads/2024/06/", "")

    def get_answer_url(self, standard, year):
        return f"{self.answer_url}/{standard}-ass-{year}.pdf"

    def get_assessment_url(self, standard, year):
        return f"{self.assessment_url}/{standard}-exm-{year}.pdf"

    def get_exemplar_url(self, standard, year, exam_type):
        return f"https://example.com/driver-no-exam"

class NoBrainTooSmall(Driver):
    def __init__(self):
        super().__init__("NoBrainTooSmall", "https://www.nobraintoosmall.co.nz/NCEA/phy3/nqfdocs/ncea-resource/schedules/", "https://www.nobraintoosmall.co.nz/NCEA/phy3/nqfdocs/ncea-resource/exams/", "")

    def get_answer_url(self, standard, year):
        return f"{self.answer_url}/{year}/{standard}-ass-{year}.pdf"

    def get_assessment_url(self, standard, year):
        return f"{self.assessment_url}/{year}/{standard}-exm-{year}.pdf"

    def get_exemplar_url(self, standard, year, exam_type):
        return f"https://example.com/driver-no-exam"

nzqa_driver = NZQA()
st_driver = StudyTime()
nbts_driver = NoBrainTooSmall()

drivers = [
    nzqa_driver,
    st_driver,
    nbts_driver
]

stats = {
    "Amount Downloaded": 0,
    "Amount Skipped": 0,
    "Amount Failed": 0,
    "Amount Missed": 0,
    "Total": 0,
    "Percentage": 0,
    "Time Taken": 0,
    "Answers Size": 0,
    "Assessment Size": 0,
    "Exemplar Size": 0,
    "Total Size": 0,
}


# Function to get standard information
def get_standard_info(standard_number):
    # Construct the URL for the specific NZQA standard
    url = f"https://www.nzqa.govt.nz/ncea/assessment/view-detailed.do?standardNumber={standard_number}"

    try:
        # Send an HTTP GET request to the NZQA website
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code == 200:

            # Parse the HTML content of the response
            soup = BeautifulSoup(response.text, 'html.parser')

            # Initialize an empty dictionary to store standard details
            info_dict = {}
            details_table = soup.find('table', {'class': 'noHover'})

            values = []

            if details_table:

                # Find all rows in the details table
                rows = details_table.find_all('tr')

                for row in rows:
                    cells = row.find_all('td')

                    # Split the contents of the second cell by the <br> tag
                    values = cells[1].text.split("\n")

                    # Remove all the whitespaces from the values and any empty values
                    values = [value.strip() for value in values if value.strip()]

            return {
                "Standard Number": standard_number,
                "Standard Title": " ".join(values[3:]).split(" (")[0].strip(),
                "Credits": values[0],
                "Assessment": values[1],
                "Level": values[2]
            }
        else:
            print("Error: Unable to fetch data from the NZQA website.")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def download_file(url, save_path):
    try:
        # Send an HTTP GET request to the PDF URL
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:

            # Open the local file for writing in binary mode
            with open(save_path, 'wb') as pdf_file:
                # Write the content of the response to the local file
                pdf_file.write(response.content)

            print(f"Downloaded '{save_path}'")
            stats["Amount Downloaded"] += 1
            return True

        else:
            print(f"Failed to download {url}. Status code: {response.status_code}")
            stats["Amount Missed"] += 1
            return False

    except Exception as e:
        print(f"An error occurred: {e}")
        stats["Amount Missed"] += 1
        return False


def download_exam(standard, year, save_path, exam_type):
    # Make the sub folders if they don't exist
    path = os.path.join(save_path, exam_type)

    if not os.path.exists(path):
        print(f"Creating directory: {path}")
        os.makedirs(path)

    current_driver = 0
    while current_driver < len(drivers):
        driver = drivers[current_driver]
        url = ""

        # If NZQA dont have the exam, try the next driver
        if driver.name != "NZQA":
            print(f"Trying {driver.name}, {standard} {year} {exam_type}, NZQA doesn't have it")

        match exam_type:
            case 'Answers':
                url = driver.get_answer_url(standard, year)

            case 'Assessment':
                url = driver.get_assessment_url(standard, year)

            case _:
                url = driver.get_exemplar_url(standard, year, exam_type)

        file = url.split("/")[-1]
        full_file = os.path.join(path, file)

        # Check if they have already been downloaded
        if os.path.exists(full_file):
            print(f"{year} {exam_type} already downloaded")
            stats["Amount Skipped"] += 1
            return

        # Try download the files
        if download_file(url, full_file):
            return

        current_driver += 1

    # No drivers have the exam
    stats["Amount Failed"] += 1


def get_size(path):
    # Initialize the total size to zero
    total_size = 0

    # Walk through the directory and its subdirectories
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            # Get the full path of the file
            file_path = os.path.join(dirpath, filename)

            # Add the file's size to the total size
            total_size += os.path.getsize(file_path)

    return total_size


def convert_size(total_size):
    for size_unit in ['B', 'KB', 'MB', 'GB', 'TB']:

        if total_size < 1024.0:
            return f"{total_size:.2f} {size_unit}"
        total_size /= 1024.0


def main(standard_numbers):
    start_time = datetime.now()

    # Run in parallel
    with ThreadPoolExecutor() as executor:
        for standard in standard_numbers:

            # Get the type of exam based on the standard number
            standard_info = get_standard_info(standard)

            # Base save path
            save_path = os.path.join(os.getcwd(), 'Saved Exams')

            # Check if the standard exists
            if not standard_info:
                print('Error: Standard not found')
                continue

            # Print the standard information
            for key, value in standard_info.items():
                print(f"{key}: {value}")

            # Get the exam info
            exam_type = standard_info['Standard Title']
            assessment = standard_info['Standard Title']

            if "," in standard_info['Standard Title']:
                assessment = standard_info['Standard Title'].split(', ')[0]
                exam_type = standard_info['Standard Title'].split(', ')[1]

            assessment += ' ' + standard

            save_path = os.path.join(save_path, exam_type)
            save_path = os.path.join(save_path, assessment)

            # Make the directory if it doesn't exist
            if not os.path.exists(save_path):
                print(f"Creating directory: {save_path}")
                os.makedirs(save_path)

            for year in YEARS:
                executor.submit(download_exam, standard, year, save_path, 'Answers')
                executor.submit(download_exam, standard, year, save_path, 'Assessment')
                executor.submit(download_exam, standard, year, save_path, 'Excellence')
                executor.submit(download_exam, standard, year, save_path, 'Merit')
                executor.submit(download_exam, standard, year, save_path, 'Achievement')

            stats["Answers Size"] += get_size(os.path.join(save_path, 'Answers'))
            stats["Assessment Size"] += get_size(os.path.join(save_path, 'Assessment'))
            stats["Total Size"] += get_size(save_path)
            stats["Exemplar Size"] += get_size(os.path.join(save_path, 'Excellence')) + get_size(os.path.join(save_path, 'Merit')) + get_size(os.path.join(save_path, 'Achievement'))

    time_taken = datetime.now() - start_time

    # Set the other stats
    stats["Time Taken"] = f"{time_taken.seconds // 60} minutes {time_taken.seconds % 60} seconds"
    stats["Answers Size"] = convert_size(stats["Answers Size"])
    stats["Assessment Size"] = convert_size(stats["Assessment Size"])
    stats["Total Size"] = convert_size(stats["Total Size"])
    stats["Exemplar Size"] = convert_size(stats["Exemplar Size"])
    stats["Total"] = stats["Amount Downloaded"] + stats["Amount Skipped"] + stats["Amount Failed"]

    if stats["Total"] != 0:
        stats["Percentage"] = f"{(stats['Amount Downloaded'] / stats['Total']) * 100:.2f}%"

    print(f"{'=' * 20} Download Complete {'=' * 20}")
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == '__main__':

    standards = []

    if len(sys.argv) > 1:
        for standard in sys.argv[1:]:

            # Check if its a number
            if not standard.isdigit():
                continue

            # Check if the standard is already in the list
            if standard not in standards:
                standards.append(standard)

    # If no standards were given, ask the user for them
    if not standards:
        while True:
            standard = input("Enter a standard number (enter 'c' to continue): ")

            if standard == 'c':

                # if there are no standards, ask the user again
                if not standards:
                    print("Error: No standards given")
                    continue
                break

            # Check if its a number
            if not standard.isdigit():
                print("Error: Invalid standard number")
                continue

            # Check if the standard is already in the list
            if standard not in standards:
                standards.append(standard)

    main(standards)
