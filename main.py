from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit, send
import eventlet
import datetime
import pytube
import os
from pathlib import Path
import random


app = Flask(__name__)
app.secret_key = "NFTHESEARCH"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

eventlet.monkey_patch()
socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")


db = SQLAlchemy(app)


class Users(db.Model):
	id = db.Column("id", db.Integer, primary_key=True)
	username = db.Column(db.String(100), nullable=False)
	password = db.Column(db.String(100), nullable=False)
	picture = db.Column(db.String(100), nullable=True)
	date = db.Column(db.String(100), nullable=False)
	email = db.Column(db.String(10), nullable=False)
	friends = db.Column(db.String, nullable=True)   # My friends
	requests = db.Column(db.String, nullable=True)  # Friends requests people sent to me (I need to accept)
	pending = db.Column(db.String, nullable=True)   # Friends requests I sent to people
	likes = db.Column(db.String, nullable=True)
	dislikes = db.Column(db.String, nullable=True)
	my_playlist = db.Column(db.String, nullable=True)


# Home page
@app.route('/')
def index():
	return render_template('index.html')


# Login page
@app.route('/login', methods=["POST", "GET"])
def login():
	error_output = ""
	if request.method == "POST":
		username = request.form["username"]
		password = request.form["password"]

		if username == "" or password == "":
			error_output = "Please fill all the fields!"
			return render_template('login.html', error_output=error_output)

		found_user = Users.query.filter_by(username=username).first()
		if not found_user:
			error_output = "Username doesn't exists!"
			return render_template('login.html', error_output=error_output)

		if found_user.password != password:
			error_output = "Wrong password!"
			return render_template('login.html', error_output=error_output)

		if 'username' in session:
			error_output = "You are already logged in!"
			return render_template('login.html', error_output=error_output)

		else:
			session['username'] = username
			return redirect(url_for("home"))

	else:
		return render_template('login.html')


# Create account page
@app.route('/register', methods=["POST", "GET"])
def register():
	error_output = ""
	if request.method == "POST":
		username = request.form["username"]
		password = request.form["password"]
		password2 = request.form["password2"]

		if username == "" or password == "" or password2 == "":
			error_output = "Please fill all the fields!"
			return render_template('register.html', error_output=error_output)

		found_user = Users.query.filter_by(username=username).first()
		if found_user:
			error_output = "This username is already taken!"
			return render_template('register.html', error_output=error_output)

		if len(password) < 8:
			error_output = "Your password has to be at least 8 characters!"
			return render_template('register.html', error_output=error_output)

		if not password.isalnum():
			error_output = "Your password has to contain only letters and numbers!"
			return render_template('register.html', error_output=error_output)

		if password != password2:
			error_output = "Make sure you wrote your password correctly!"
			return render_template('register.html', error_output=error_output)

		else:
			creation_date = datetime.datetime.now().date()
			creation_date = str(creation_date).split('-')
			fixed_date = creation_date[2] + '.' + creation_date[1] + '.' + creation_date[0]

			user = Users(username=username, password=password, picture="images/DefaultPFP.png", date=fixed_date, email="You haven't added an email yet", friends="", requests="", pending="", likes="", dislikes="", my_playlist="")
			db.session.add(user)
			db.session.commit()
			return redirect(url_for("login"))

	else:
		return render_template('register.html')


@app.route('/logout')
def logout():
	session.pop('username', None)
	return redirect(url_for("login"))


@app.route('/home', methods=["POST", "GET"])
def home():
	if 'username' in session:
		username = session['username']

		playlist = os.listdir('D:\Discord Project\static\music')

		return render_template("home.html", user=username, playlist=playlist)

	else:
		return redirect(url_for("login"))


@app.route('/home/<string:song>')
def watch(song):
	if 'username' in session:
		username = session['username']

		playlist = os.listdir('D:\Discord Project\static\music')
		all_users = Users.query.all()
		song_likes = 0
		song_dislikes = 0

		for user in all_users:
			print(user.likes)
			if user.likes is not None and song in user.likes:
				song_likes += 1
			print(user.dislikes)
			if user.dislikes is not None and song in user.dislikes:
				song_dislikes += 1

		found_user = Users.query.filter_by(username=username).first()
		liked_songs = found_user.likes
		disliked_songs = found_user.dislikes
		if found_user.my_playlist is not None:
			my_playlist = found_user.my_playlist.split(',')
		else:
			my_playlist = ""

		return render_template('watch.html', playlist=playlist, song=song, song_likes=song_likes, song_dislikes=song_dislikes, liked_songs=liked_songs, disliked_songs=disliked_songs, my_playlist=my_playlist)

	else:
		return redirect(url_for("login"))


# Live music and global chat page
@app.route('/live', methods=["POST", "GET"])
def live():
	error_output = ""
	new_list = []
	if 'username' in session:
		username = session['username']

		with open("globalchat.txt", 'r') as read_messages:
			read_messages = read_messages.read()
			split_messages = read_messages.split('\n')

		playlist = os.listdir('D:\Discord Project\static\music')
		random.shuffle(playlist)

		print(playlist)

		return render_template("live.html", user=username, messages=split_messages, playlist=playlist)

	else:
		return redirect(url_for("login"))


@app.route('/playlist', methods=["POST", "GET"])
def user_playlist():
	if 'username' in session:
		username = session['username']

		found_user = Users.query.filter_by(username=username).first()

		if found_user.my_playlist is not None:
			playlist = found_user.my_playlist.split(',')
			first_song = playlist[0]
			playlist_length = len(playlist) - 1
		else:
			playlist = ""
			first_song = ""
			playlist_length = 0

		return render_template("playlists.html", playlist=playlist, first_song=first_song, playlist_length=playlist_length)

	else:
		return redirect(url_for("login"))


@app.route('/playlist/<string:song>')
def song_from_playlist(song):
	if 'username' in session:
		username = session['username']

		found_user = Users.query.filter_by(username=username).first()

		if found_user.my_playlist is not None:
			playlist = found_user.my_playlist.split(',')
		else:
			playlist = ""

		print(playlist)

		return render_template('playlist.html', playlist=playlist, song=song)

	else:
		return redirect(url_for("login"))


@app.route('/new')
def new():
	if 'username' in session:
		username = session['username']

		sorted_files = sorted(Path('D:/Discord Project/static/music').iterdir(), key=os.path.getmtime, reverse=True)
		playlist = []

		for song_path in sorted_files:
			song_path = str(song_path).replace('D:\\Discord Project\\static\\music\\', '').replace('.mp4', '')
			playlist.append(song_path)

		return render_template("new.html", user=username, playlist=playlist)

	else:
		return render_template('login.html')


# Upload page
@app.route('/upload', methods=["POST", "GET"])
def upload():
	if 'username' in session:
		username = session['username']

		if request.method == "POST":
			song_url = request.form["upload"]
			output_message = ""

			if song_url == "":
				output_message = "Please Enter a YouTube Link"

			else:
				try:
					song_url_title = pytube.YouTube(song_url).title
					song_url_title = song_url_title.replace('.', '')
					song_url_title = song_url_title.replace("'", '')
					song_url_title = song_url_title + '.mp4'
					playlist = os.listdir('D:\Discord Project\static\music')
					print(song_url_title)
					print(playlist)
					if song_url_title.replace(',', '') in playlist:
						output_message = "Someone Already Uploaded This Song... Try Another Song"
						return render_template("upload.html", user=username, output_message=output_message, song_url_title=song_url_title.replace(',', ''))
					else:
						try:
							pytube.YouTube(song_url).streams.get_highest_resolution().download('static/music')
							output_message = "Your Song Has Been Uploaded!"
							return render_template("upload.html", user=username, output_message=output_message, song_url_title=song_url_title.replace(',', ''))
						except:
							output_message = "Please Enter a Valid YouTube Link"
				except:
					output_message = "Please Enter a Valid YouTube Link"

			return render_template("upload.html", user=username, output_message=output_message)

		return render_template("upload.html")

	else:
		return render_template('login.html')


@app.route('/friends')
def friends():
	if 'username' in session:
		username = session['username']

		found_user = Users.query.filter_by(username=username).first()

		if found_user.friends is not None:
			friends_list = found_user.friends.split(',')
		else:
			friends_list = []
		if found_user.requests is not None:
			new_requests = len(found_user.requests.split(',')) - 1
		else:
			new_requests = 0

		return render_template('friends.html', friends_list=friends_list, new_requests=new_requests)

	else:
		return redirect(url_for("login"))


@app.route('/friends/<friend>')
def DM(friend):
	if 'username' in session:
		username = session['username']

		my_user = Users.query.filter_by(username=username).first()
		friends_list = my_user.friends.split(',')
		print(friend)

		friend_user = Users.query.filter_by(username=friend).first()
		friend_picture = friend_user.picture

		friend_date = friend_user.date

		if my_user.friends is not None:
			my_friends = my_user.friends.split(',')
		else:
			my_friends = ""
		if friend_user.friends is not None:
			friend_friends = friend_user.friends.split(',')
		else:
			friend_friends = ""
		mutual_friends = ""

		for f in my_friends:
			if f in friend_friends and f != "":
				if mutual_friends != "":
					mutual_friends += ', ' + f
				else:
					mutual_friends += f
		if mutual_friends == "":
			mutual_friends = "No mutual friends"

		# Check matching percentage
		if my_user.my_playlist is not None:
			playlist1 = my_user.my_playlist.split(',')
		else:
			playlist1 = []
		if friend_user.my_playlist is not None:
			playlist2 = friend_user.my_playlist.split(',')
		else:
			playlist2 = []
		if my_user.likes is not None:
			liked1 = my_user.likes.split(',')
		else:
			liked1 = []
		if friend_user.likes is not None:
			liked2 = friend_user.likes.split(',')
		else:
			liked2 = []

		matching_percentage = check_match(playlist1, playlist2, liked1, liked2)

		return render_template('dms.html', friends_list=friends_list, friend_name=friend, friend_picture=friend_picture, friend_date=friend_date, mutual_friends=mutual_friends, matching_percentage=matching_percentage)

	else:
		return redirect(url_for("login"))


@app.route('/profile', methods=["POST", "GET"])
def profile():
	if 'username' in session:
		username = session['username']

		found_user = Users.query.filter_by(username=username).first()

		error_output = ""
		updated_info = ""
		picture = found_user.picture
		email_temp = found_user.email

		if request.method == "POST":
			new_username = request.form["changeUsername"]
			new_picture = request.form["changePicture"]
			email = request.form["changeEmail"]
			password = request.form["changePassword"]
			password2 = request.form["changePassword2"]
			current_password = request.form["confirmation"]

			found_new_user = Users.query.filter_by(username=new_username).first()

			if current_password == "":
				error_output = "Please enter your current password to confirm the changes"
				return render_template('profile.html', error_output=error_output, user=username, picture=picture, email=email_temp)

			if current_password == found_user.password:

				if new_username != "":
					if not found_new_user:
						found_user.username = new_username
						db.session.commit()
						session['username'] = new_username
						updated_info += "Congratulations on your new USERNAME! \n"

					else:
						error_output += "This username is already taken! \n"

				if new_picture != "":
					if new_picture.split('.')[-1] == "png" or new_picture.split('.')[-1] == "jpg" or new_picture.split('.')[-1] == "jpeg":
						found_user.picture = new_picture
						db.session.commit()
						picture = new_picture
						updated_info += "Congratulations on your new PROFILE PICTURE! \n"
					else:
						error_output += "Please enter a working picture URL! \n"

				if email != "":
					found_user.email = email
					db.session.commit()
					updated_info = "Updated your EMAIL successfully"
					email_temp = found_user.email

				if password != "" and password2 != "":
					if password == password2:
						found_user.password = password
						db.session.commit()
						updated_info += "Updated your PASSWORD successfully \n"
					else:
						error_output += "Make sure you wrote your password correctly! \n"

				return render_template('profile.html', error_output=error_output, confirmation_output=updated_info, user=session['username'], picture=picture, email=email_temp)

			else:
				error_output = "Please make sure you wrote your CURRENT password correctly!"
				return render_template('profile.html', error_output=error_output, user=username, picture=picture, email=email_temp)

		else:
			return render_template('profile.html', user=username, picture=picture, email=email_temp)

	else:
		return redirect(url_for("login"))


@app.route('/search', methods=["POST", "GET"])
def search():
	if 'username' in session:
		username = session['username']

		if request.method == "POST":

			# check if the POST method was from adding/accepting friend request and get the username and action(add/accept)
			try:
				get_search = ""
				friend_request = request.form["friend"]
				print(friend_request)
				friend_request = friend_request.split(',')

				# when sending friend request:
				# add his username to my pending requests and my username to his friend requests
				if friend_request[1] == "Add":
					my_user = Users.query.filter_by(username=username).first()
					if my_user.pending is None:
						my_user.pending = friend_request[0] + ','
					else:
						my_user.pending += friend_request[0] + ','
					db.session.commit()

					friend_user = Users.query.filter_by(username=friend_request[0]).first()
					if friend_user.requests is None:
						friend_user.requests = username + ','
					else:
						friend_user.requests += username + ','
					db.session.commit()

				# when accepting friend request:
				# remove his name from my pending requests, my username from his friend requests and add each other as friends
				if friend_request[1] == "Accept":
					my_user = Users.query.filter_by(username=username).first()
					my_user.requests = my_user.requests.replace(friend_request[0] + ',', '')
					if my_user.friends is None:
						my_user.friends = friend_request[0] + ','
					else:
						my_user.friends += friend_request[0] + ','
					db.session.commit()

					friend_user = Users.query.filter_by(username=friend_request[0]).first()
					friend_user.pending = friend_user.pending.replace(username + ',', '')
					friend_user.friends += username + ','
					db.session.commit()

			# get the username that was search
			except:
				get_search = request.form["searchKey"]

			all_users = Users.query.all()
			found_users_list = []

			if Users.query.filter_by(username=username).first().friends is None:
				my_friends = ""
			else:
				my_friends = Users.query.filter_by(username=username).first().friends.split(',')
			if Users.query.filter_by(username=username).first().requests is None:
				firnd_requests = ""
			else:
				firnd_requests = Users.query.filter_by(username=username).first().requests.split(',')
			if Users.query.filter_by(username=username).first().pending is None:
				pending_requests = ""
			else:
				pending_requests = Users.query.filter_by(username=username).first().pending.split(',')

			# get all the users that match the search key from the database
			# and create a list with their username, picture, user creation date and situation(friend/pending/not friend)
			for user in all_users:
				if get_search in user.username:
					if user.username == username:
						pass

					else:
						my_user = Users.query.filter_by(username=username).first()
						friend_user = Users.query.filter_by(username=user.username).first()

						# Check mutual friends
						if my_user.friends is not None:
							my_friends = my_user.friends.split(',')
						else:
							my_friends = ""
						if friend_user.friends is not None:
							friend_friends = friend_user.friends.split(',')
						else:
							friend_friends = ""
						mutual_friends = ""

						for f in my_friends:
							if f in friend_friends and f != "":
								if mutual_friends != "":
									mutual_friends += ', ' + f
								else:
									mutual_friends += f
						if mutual_friends == "":
							mutual_friends = "No mutual friends"

						# Check matching percentage
						if my_user.my_playlist is not None:
							playlist1 = my_user.my_playlist.split(',')
						else:
							playlist1 = []
						if friend_user.my_playlist is not None:
							playlist2 = friend_user.my_playlist.split(',')
						else:
							playlist2 = []
						if my_user.likes is not None:
							liked1 = my_user.likes.split(',')
						else:
							liked1 = []
						if friend_user.likes is not None:
							liked2 = friend_user.likes.split(',')
						else:
							liked2 = []

						matching_percentage = check_match(playlist1, playlist2, liked1, liked2)

						if user.username in my_friends:
							found_users_list.append([user.username, user.picture, user.date, mutual_friends, matching_percentage, "Friend"])
						elif user.username in firnd_requests:
							found_users_list.append([user.username, user.picture, user.date, mutual_friends, matching_percentage, "Accept"])
						elif user.username in pending_requests:
							found_users_list.append([user.username, user.picture, user.date, mutual_friends, matching_percentage, "Pending"])
						else:
							found_users_list.append([user.username, user.picture, user.date, mutual_friends, matching_percentage, "Add"])

			print(found_users_list)

			return render_template('search.html', found_users_list=found_users_list)

		else:
			return redirect(url_for("friends"))

	else:
		return redirect(url_for("login"))


@app.route('/friends/requests', methods=["POST", "GET"])
def requests():
	if 'username' in session:
		username = session['username']

		found_user = Users.query.filter_by(username=username).first()
		if found_user.requests is not None:
			friend_requests = found_user.requests.split(',')
		else:
			friend_requests = []
		if found_user.pending is not None:
			pending_requests = found_user.pending.split(',')
		else:
			pending_requests = []
		friend_requests_pictures = []
		pending_requests_pictures = []

		for fr in friend_requests:
			if fr != "":
				found_user = Users.query.filter_by(username=fr).first()
				friend_requests_pictures.append(found_user.picture)

		for pr in pending_requests:
			if pr != "":
				found_user = Users.query.filter_by(username=pr).first()
				pending_requests_pictures.append(found_user.picture)

		friend_requests_length = len(friend_requests)
		pending_requests_length = len(pending_requests)

		if request.method == "POST":
			friend_request = request.form["action"]
			friend_request = friend_request.split(',')

			# remove his name from my pending requests, my username from his friend requests and add each other as friends
			if friend_request[1] == "accept":
				my_user = Users.query.filter_by(username=username).first()
				my_user.requests = my_user.requests.replace(friend_request[0] + ',', '')
				if my_user.friends is not None:
					my_user.friends += friend_request[0] + ','
				else:
					my_user.friends = friend_request[0] + ','
				db.session.commit()

				friend_user = Users.query.filter_by(username=friend_request[0]).first()
				friend_user.pending = friend_user.pending.replace(username + ',', '')
				if friend_user.friends is not None:
					friend_user.friends += username + ','
				else:
					friend_user.friends = username + ','
				db.session.commit()

			# remove his name from my requests and my name from his pending
			elif friend_request[1] == "ignore":
				my_user = Users.query.filter_by(username=username).first()
				my_user.requests = my_user.requests.replace(friend_request[0] + ',', '')
				db.session.commit()

				friend_user = Users.query.filter_by(username=friend_request[0]).first()
				friend_user.pending = friend_user.pending.replace(username + ',', '')
				db.session.commit()

			# remove his name from my pending and my name from his requests
			elif friend_request[1] == "cancel":
				my_user = Users.query.filter_by(username=username).first()
				my_user.pending = my_user.pending.replace(friend_request[0] + ',', '')
				db.session.commit()

				friend_user = Users.query.filter_by(username=friend_request[0]).first()
				if friend_user.requests is not None:
					friend_user.requests = friend_user.requests.replace(username + ',', '')
				db.session.commit()

			found_user = Users.query.filter_by(username=username).first()
			if found_user.requests is not None:
				friend_requests = found_user.requests.split(',')
			if found_user.pending is not None:
				pending_requests = found_user.pending.split(',')

			friend_requests_length = len(friend_requests)
			pending_requests_length = len(pending_requests)

		return render_template('requests.html', friend_requests=friend_requests, friend_requests_pictures=friend_requests_pictures, pending_requests=pending_requests, pending_requests_pictures=pending_requests_pictures, friend_requests_length=friend_requests_length, pending_requests_length=pending_requests_length)

	else:
		return redirect(url_for("login"))


def check_match(playlist1, playlist2, liked_songs1, liked_songs2):
	if len(playlist1) == 1 or len(playlist2) == 1:
		mutual_playlist_percentage = 0
	else:
		mutual_songs_in_playlist = 0
		for song in playlist2:
			if song in playlist1:
				mutual_songs_in_playlist += 1
		mutual_playlist_percentage = mutual_songs_in_playlist/len(playlist1)*100

	if len(liked_songs1) == 1 or len(liked_songs2) == 1:
		mutual_likes_percentage = 0
	else:
		mutual_liked_songs = 0
		for song in liked_songs2:
			if song in liked_songs1:
				mutual_liked_songs += 1
		mutual_likes_percentage = mutual_liked_songs/len(liked_songs1)*100

	print(mutual_playlist_percentage)
	print(mutual_likes_percentage)

	return round((mutual_playlist_percentage + mutual_likes_percentage)/2)


@socketio.on('connect')
def connect():
	print("Connected!")


@socketio.on('disconnect')
def disconnect():
	print("Disconnected!")


@socketio.on('message')
def handleMessage(msg):
	print('Message: ' + msg)
	username = session['username']

	if msg.split(' ', 1)[0] == "!play":
		url = msg.split(' ')[1]
		pytube.YouTube(url).streams.get_highest_resolution().download('static/music')
		add_song_message = username + " added a song to the queue"
		print(add_song_message)
		emit("songMessage", add_song_message, broadcast=True)

	else:
		# get user's profile picture
		found_user = Users.query.filter_by(username=username).first()
		user_picture = found_user.picture

		# get when the message was sent and fix structure (date and time)
		message_date = datetime.datetime.now().date()
		message_date = str(message_date).split('-')
		fixed_date = message_date[2] + '.' + message_date[1] + '.' + message_date[0]
		print(fixed_date)

		message_time = datetime.datetime.now().time()
		message_time = str(message_time).split(':')
		fixed_time = message_time[0] + ':' + message_time[1]
		print(fixed_time)

		global_chat_db = open("globalchat.txt", "a")
		global_chat_db.write(user_picture + ' ' + username + ' ' + fixed_date + ' ' + fixed_time + ' ' + msg + '\n')
		global_chat_db.close()

		full_message = [user_picture, username, fixed_date, fixed_time, msg]
		emit("liveMessage", full_message, broadcast=True)


@socketio.on('addSongToPlaylist')
def addToPlaylist(song_name):

	username = session['username']
	found_user = Users.query.filter_by(username=username).first()

	if found_user.my_playlist is None:
		found_user.my_playlist = song_name + ','
	else:
		found_user.my_playlist += song_name + ','
	db.session.commit()

	print(found_user.my_playlist)


@socketio.on('removeSongFromPlaylist')
def removeFromPlaylist(song_name):

	username = session['username']
	found_user = Users.query.filter_by(username=username).first()

	if song_name in found_user.my_playlist:
		found_user.my_playlist = found_user.my_playlist.replace(song_name + ',', '')
		db.session.commit()
	else:
		pass

	print(found_user.my_playlist)


@socketio.on('addSongToLikes')
def addToLikes(song_name):

	username = session['username']
	found_user = Users.query.filter_by(username=username).first()

	if found_user.likes is None:
		found_user.likes = song_name + ','
	else:
		found_user.likes += song_name + ','
	if found_user.dislikes is not None and song_name in found_user.dislikes:
		found_user.dislikes = found_user.dislikes.replace(song_name + ",", "")
	db.session.commit()

	print(found_user.likes)
	print(found_user.dislikes)


@socketio.on('removeSongFromLikes')
def removeFromLikes(song_name):

	username = session['username']
	found_user = Users.query.filter_by(username=username).first()

	found_user.likes = found_user.likes.replace(song_name + ",", "")
	db.session.commit()

	print(found_user.likes)
	print(found_user.dislikes)


@socketio.on('addSongToDislikes')
def addToDislikes(song_name):

	username = session['username']
	found_user = Users.query.filter_by(username=username).first()

	if found_user.dislikes is None:
		found_user.dislikes = song_name + ','
	else:
		found_user.dislikes += song_name + ','

	if found_user.likes is not None and song_name in found_user.likes:
		found_user.likes = found_user.likes.replace(song_name + ",", "")
	db.session.commit()

	print(found_user.likes)
	print(found_user.dislikes)


@socketio.on('removeSongFromDislikes')
def removeFromDislikes(song_name):

	username = session['username']
	found_user = Users.query.filter_by(username=username).first()

	found_user.dislikes = found_user.dislikes.replace(song_name + ",", "")
	db.session.commit()

	print(found_user.likes)
	print(found_user.dislikes)


if __name__ == '__main__':
	db.create_all()
	socketio.run(app, host="0.0.0.0", port='5000', debug=True)
