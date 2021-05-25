#########################################
#  nama  : MUHAMMAD RIZKY RAHMATTULLAH	#
#  email : MASTAHRIZKY@GMAIL.COM 		#
#########################################

#ada catatan di bawah sendiri. terimakasih

import tweepy
import re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import csv
import sqlite3
from datetime import datetime, timedelta

def create_db():
	connection = sqlite3.connect("data_tmp.db")
	create_film_table = '''CREATE TABLE IF NOT EXISTS tweets (
								id INTEGER PRIMARY KEY AUTOINCREMENT,
								tweet TEXT NOT NULL,
								username TEXT NOT NULL,
								waktu TEXT NOT NULL,
								sentiment INTEGER,
                                unique(tweet,username,waktu));'''

	cursor = connection.cursor()
	cursor.execute(create_film_table)
	connection.commit()
	cursor.close()
	connection.close()

def insert_to_db(data):
    connection = sqlite3.connect("data_tmp.db")
    cursor = connection.cursor()
    sql = ''' INSERT OR IGNORE INTO tweets VALUES(NULL,?,?,?,NULL)'''
    cursor.executemany(sql, data)
    connection.commit()
    cursor.close()
    connection.close()


def processTweet(tweet):	
	#di rubah ke huruf kecil
	tweet = tweet.lower()
	#menghapus url
	tweet = re.sub('((www\.[^\s]+)|(https?://[^\s]+))','',tweet)
	#hapus username
	tweet = re.sub('@[^\s]+','',tweet)    
	#hapus white space
	tweet = re.sub('[\s]+', ' ', tweet)
	#ganti tag jadi kata biasa
	tweet = re.sub(r'#([^\s]+)', r'\1', tweet)
	#trim
	tweet = tweet.strip('\'"')
	return tweet

def update_data():
	consumer_key = ""
	consumer_secret = ""
	access_token = ""
	access_token_secret = ""

	#otentikasi ke api twitter
	auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
	auth.set_access_token(access_token, access_token_secret)
	api = tweepy.API(auth)

	#mengambil tanggal sekarang hingga 3 hari kebelakang
	sekarang = datetime.now()
	kemarin = sekarang - timedelta(3)

	start = sekarang.strftime("%Y-%m-%d")
	end   = kemarin.strftime("%Y-%m-%d")
    
	print(f'proses mengambil tweet hari ini {start} hingga {end} (3 hari)')

	#kata pencarian dan tidak menampilkan retweets
	search_words = "vaksin covid"
	new_search = search_words + " -filter:retweets"

	#proses mengambil tweet dengan tweepy berdasarkan kata pencarian 'vaksin covid' 
	#dan range tanggal 3 hari kebelakang di mulai hari script di jalankan.
	tweets = tweepy.Cursor(api.search,
			q=new_search,
			lang="id",
			since=end,
			until=start,
			result_type="recent",
			count=100,
			tweet_mode='extended').items()

	tweets_list = []
	username = []
	waktu = []

	#membersih kan tweet dan memasukkan ke array
	for tweet in tweets:
		tweets_list.append(processTweet(tweet.full_text))
		username.append(tweet.author._json['screen_name'])
		waktu.append(tweet.created_at)

	#masukkan data ke database sekaligus menggunakan executemany
	insert_to_db(list(zip(tweets_list, username, waktu)))

    


def update_nilai_sentiment():

	#koneksi ke database sqlite dan mengambil semua data dari database
	conn = sqlite3.connect('data_tmp.db')
	my_df = pd.read_sql('select * from tweets', conn)

	#membaca file kata positif dan negatif
	pos_list= open("./kata_positif.txt","r")
	pos_kata = pos_list.readlines()
	neg_list= open("./kata_negatif.txt","r")
	neg_kata = neg_list.readlines()

	S = []

	#proses untuk menilai sentiment
	for item in my_df['tweet']:
			count_p = 0
			count_n = 0
			for kata_pos in pos_kata:
				if kata_pos.strip() in item:
					count_p +=1
			for kata_neg in neg_kata:
				if kata_neg.strip() in item:
					count_n +=1
			S.append(count_p - count_n)

	#menambahkan hasil array sentiment ke dalam dataframe
	my_df["sentiment"] = S

	#update data ke database bagian sentiment yang kosong
	crud_query = '''update tweets set tweet=?, username=?, waktu=?, sentiment=? where id = ?'''
	cursor = conn.cursor()
	cursor.executemany(crud_query,list(zip(my_df.tweet, my_df.username, my_df.waktu, my_df.sentiment, my_df.id)))
	conn.commit()
	cursor.close()
	conn.close()



def lihat_data():
	#koneksi ke database sqlite
	conn = sqlite3.connect('data_tmp.db')

	#memasukkan range waktu yang nanti di gunakan untuk menambil data
	al_awal = input('tanggal awal (format: 2020-08-24 ) : ')
	al_akhir = input('tanggal akhir (format: 2020-08-24 ) : ')

	#mengambil data tweet berdasarkan range waktu
	query = f"SELECT * FROM tweets WHERE date(waktu) BETWEEN '{al_awal}' AND '{al_akhir}'"
	my_df = pd.read_sql(query, conn)
	print(my_df)
	conn.close()



def Visualisasi():
	#memasukkan range waktu yang nanti di gunakan untuk menambil data
	al_awal = input('tanggal awal (format: 2020-08-24 ) : ')
	al_akhir = input('tanggal akhir (format: 2020-08-24 ) : ')

	#mengambil data tweet berdasarkan range waktu
	conn = sqlite3.connect('data_tmp.db')
	query = f"SELECT * FROM tweets WHERE date(waktu) BETWEEN '{al_awal}' AND '{al_akhir}'"
	my_df = pd.read_sql(query, conn)

	#menampilkan nilai rata rata, median dan standart deviasi
	print ("Nilai rata-rata: "+str(np.mean(my_df['sentiment'])))
	print ("Nilai median   : "+str(np.median(my_df['sentiment'])))
	print ("Standar deviasi: "+str(np.std(my_df['sentiment'])))

	#memviasualisasi kan data nilai sentiment
	labels, counts = np.unique(my_df['sentiment'], return_counts=True)
	plt.bar(labels, counts, align='center')
	plt.gca().set_xticks(labels)
	plt.show()
	conn.close()

    


def menu():
	print('''apa yang anda ingin lakukan ?
	1. Update Data
	2. Update Nilai Sentiment
	3. Lihat Data
	4. Visualisasi
	5. Keluar''')

	jwb = input('>> ')

	if jwb == '1':
		update_data()
		print('\n\n')
		menu()


	elif jwb == '2':
		update_nilai_sentiment()
		print('\n\n')
		menu()

	elif jwb == '3':
		lihat_data()
		print('\n\n')
		menu()

	elif jwb == '4':
		Visualisasi()
		print('\n\n')
		menu()

	elif jwb == '5':
		exit()
		

	else:
		print('\n\n')
		print("enggak ada")
		menu()


if __name__ == "__main__":
	create_db()
	menu()

#   CATATAN

#pada create tabel di 3 kolom (username, tweet, waktu) saya bikin unique biar ketika saya update data 
#tidak ada data yang dobel dan hanya di masukkan data yang baru / belum ada di database
#sehingga pas bagian insert saya menggunakan insert or ignore into

#dan juga di bagian update sentiment. ini yang paling ngeselin. sebelumnya saya menggunakan panda
#dari dataframe ke sql sehingga pas saya update datanya malah dobel lagi
#entah kenapa sifat unique yang sudah saya buat jadi hilang
#sehingga saya rubah menggunakan executemany()

#bagian tampilkan data saya tampilkan semua biar lebih enak untuk pengecekan data eror karena update data.
#tanpa harus membuka sqlitebrowser.

#selebihnya masih sama sesuai penjelasan di pdf dan apa yang sudah saya pelajari di sanbercode.com terimakasih
#email saya sebelumnya Nudinrizwan@gmail.com sudah saya ganti di sanber jadi mastahrizky@gmail.com
