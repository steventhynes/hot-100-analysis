import datetime
import requests
import pprint
import pickle
import re
from scipy.stats import zipf

base_url = "https://www.billboard.com/charts/hot-100/"
start_date = datetime.datetime(1958, 8, 4)
end_date = datetime.datetime.today() - datetime.timedelta(1)
# end_date = datetime.datetime(1959, 4, 13)

current_date = start_date
ranks = {}

try:
    data_pickle = open("data.txt", "rb")
    loaded_data = pickle.load(data_pickle)
    data_pickle.close()
    ranks = loaded_data[0]
    current_date = loaded_data[1] + datetime.timedelta(7)
    print("Data pickle loaded.")
except FileNotFoundError:
    print("No pickle file found.")
except EOFError:
    print("Pickle load failed - ran out of input.")

while current_date <= end_date:
    current_url = base_url + "{}-{:02d}-{:02d}".format(current_date.year, current_date.month, current_date.day)
    page_text = requests.get(current_url).text
    print("Visiting " + str(current_date))
    if "o-chart-results-list-row-container" in page_text:
        print("Data found.")
        split_by_entry = page_text.split("<li class=\"lrv-u-width-100p\">")
        print(len(split_by_entry))
        for rank in range(1, 101):
            try:
                after_split = re.split("<|>", split_by_entry[rank])
                # print(after_split)
                song = after_split[6].strip()
                artist = after_split[10].strip()
                print("{0} rank {1}\tSong: {2}\tArtist: {3}".format(current_date, rank, song, artist))
                if (song, artist) not in ranks:
                    ranks[(song, artist)] = {"debut": current_date, "weeks": {}}
                ranks[(song, artist)]["weeks"][str(current_date)] = rank
            except IndexError:
                print("Missing rank?")
        # pprint.pprint(ranks)
        data_pickle = open("data.txt", "wb")
        pickle.dump((ranks, current_date), data_pickle)
        data_pickle.close()
        print("Data written to file.")
        current_date += datetime.timedelta(7)
    else:
        print("No data found.")

rank_freqs = [0] * 100

for entry in ranks:
    current_high = 101
    for week in ranks[entry]["weeks"]:
        if ranks[entry]["weeks"][week] < current_high:
            current_high = ranks[entry]["weeks"][week]
    ranks[entry]["peak"] = current_high
    for i in range(100, 0, -1):
        if i < current_high:
            break
        rank_freqs[i - 1] += 1

rank_probs = [k / rank_freqs[-1] for k in rank_freqs]

for entry in ranks:
    score = 0.0
    for week in ranks[entry]["weeks"]:
        score += 1 / rank_probs[ranks[entry]["weeks"][week] - 1]
    ranks[entry]["score"] = score


ordering = sorted(ranks, key=lambda x: ranks[x]["score"], reverse=True)

a_file = open("output.csv", "w")
a_file.write("rank,song,artist,score,debut,peak\n")

for i in range(len(ordering)):
    a_file.write('{},"{}","{}",{},{},{}\n'.format(i + 1, ordering[i][0], ordering[i][1], str(ranks[ordering[i]]["score"]), str(ranks[ordering[i]]["debut"])[:7], str(ranks[ordering[i]]["peak"])))

a_file.close()

b_file = open("rawdata.txt", "w")
b_file.write(str(ranks))

b_file.close()


