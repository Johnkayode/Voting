# Copyright Fortior Blockchain, LLLP 2021
# Open Source under Apache License
   
from flask import request, render_template, redirect, url_for, flash, session
from flask.helpers import make_response

from sqlalchemy import func
from algosdk import account, encoding, mnemonic
from . import db
from .decorators import is_admin
from .vote import election_voting, hashing, count_votes
from .vote import reset_votes, reset_corporate_votes
from .models import Admin, Voter, Candidate, Election
from .utils import *
from algosdk.future.transaction import AssetTransferTxn, PaymentTxn
from algosdk.v2client import algod

import matplotlib
import matplotlib.pyplot as plt
from flask import current_app as app



@app.route("/")
def home():
	""" Start page """
	return render_template('index.html')

@app.route("/admin/register", methods = ['POST', 'GET'])
def admin_register():
	if request.method == "POST":
		first_name = request.form.get("first_name")
		last_name = request.form.get("last_name")
		email = request.form.get("email")
		password = request.form.get("password")
		
		admin = Admin.query.filter_by(email=email).first()
		if admin:
			flash("Email already exists", "danger")
			return redirect(url_for("admin_register"))
		admin = Admin(first_name=first_name, last_name=last_name, email=email, password=hashing(password))
		db.session.add(admin)
		db.session.commit()

		flash("Admin account successfully created", "success")
		return redirect(url_for("admin_login"))
	
	return render_template("admin_register.html")

@app.route("/admin/login", methods = ['POST', 'GET'])
def admin_login():
	if request.method == "POST":
		email = request.form.get("email")
		password = request.form.get("password")
		
		admin = Admin.query.filter_by(email=email).first()
		if not admin or admin.password != hashing(password):
			flash("Account does not exist", "danger")
			return redirect(url_for("admin_login"))
		
		session["admin"] = admin.email
		flash("Logged in successfully", "success")
		return redirect(url_for("home"))
	
	return render_template("admin_login.html")

@app.route("/admin/logout", methods = ['GET'])
def admin_logout():
	session.pop("admin")
	flash("Logged out successfully", "info")
	return redirect(url_for("admin_login"))
	

@app.route('/voter/create', methods = ['POST','GET'])
@is_admin
def create_voter():
	if request.method == 'POST':
		first_name = request.form.get('first_name')
		last_name = request.form.get('last_name')
		matric_no = request.form.get('matric_no')
		department = request.form.get('department')
		voter = Voter.query.filter_by(matric_no=matric_no).first()
		if voter:
			flash("Voter already exists", "danger")
			return redirect(url_for("create_voter"))
		voter = Voter(first_name=first_name, last_name=last_name, matric_no=matric_no, department=department)
		db.session.add(voter)
		db.session.commit()
		flash("Voter created", "success")
		return redirect(url_for("create_voter"))
		
	return render_template('create_voter.html')

@app.route('/elections', methods = ['GET'])
def elections():
	elections = Election.query.all()
	return render_template('elections.html', elections=elections)

@app.route('/elections/<slug>', methods = ['GET'])
def election_detail(slug):
	election = Election.query.filter_by(slug=slug).first()
	return render_template('election.html', election=election)

@app.route('/election/create', methods = ['POST','GET'])
@is_admin
def create_election():
	if request.method == 'POST':
		title = request.form.get('title')
		slug =  slugify(title)
		admin_email = session.get("admin", "")
		admin = Admin.query.filter_by(email=admin_email).first()
		election = Election(admin_id=admin.id, title=title, slug=slug, voters="")
		db.session.add(election)
		db.session.commit()
		flash("Election created", "success")
		return redirect(url_for("create_election"))
		
	return render_template('create_election.html')

@app.route('/candidate/create', methods = ['POST','GET'])
@is_admin
def create_candidate():
	if request.method == 'POST':
		first_name = request.form.get('first_name')
		last_name = request.form.get('last_name')
		manifesto = request.form.get('manifesto')
		election_id = request.form.get('election')
		election = Election.query.filter_by(id=election_id).first()
		try:
			address, phrase, private_key = generate_algorand_keypair()
			print(phrase)
			choice_coin_opt_in(address, private_key)
			candidate = Candidate(election_id=election_id, 
				first_name=first_name, 
				last_name=last_name, 
				manifesto=manifesto,
				address=address,
				passphrase=phrase
			)
			db.session.add(candidate)
			db.session.commit()
			flash("Candidate created", "success")
			return redirect(election.get_absolute_url)
		except Exception as e:
			flash(e, "danger")
			return redirect(election.get_absolute_url)

	admin_email = session.get("admin", "")
	admin = Admin.query.filter_by(email=admin_email).first()
	elections = Election.query.filter_by(admin=admin, is_open=True).all()
	return render_template('create_candidate.html', elections=elections)


@app.route('/end/<slug>', methods = ['GET'])
@is_admin
def end(slug):
	election = Election.query.filter_by(slug=slug).first()
	if session["admin"] == election.admin.email:
		labels, votes = count_votes(election.candidates)
		print("Votes: ", votes)
		session["labels"] = labels
		session["votes"] = votes
		for candidate in election.candidates:
			reset(candidate.address, candidate.passphrase, candidate.votes)
		election.is_open = False
		db.session.commit()
		return redirect(election.get_absolute_url)


	
@app.route('/result/<slug>', methods = ['GET'])
def result(slug):
	election = Election.query.filter_by(slug=slug).first()
	winner = max(election.candidates, key=lambda candidate:candidate.votes)
	candidates = session.get("labels")
	votes = session.get("votes")
	return render_template("result.html", candidates=candidates, votes=votes, winner = winner)

@app.route('/vote/<id>', methods = ['POST'])
def vote(id):
	matric_no = request.form.get('matric_no')
	candidate = Candidate.query.get(id)
	voter = Voter.query.filter_by(matric_no=matric_no).first()
	if not voter:
		flash("You are not a registered voter", "danger")
		return redirect(candidate.election.get_absolute_url)
	# Check if voter has voted for the election
	if str(matric_no) in str(candidate.election.voters).split():
		flash("Your vote has been counted already.", "danger")
		return redirect(candidate.election.get_absolute_url)


	message = vote_candidate(candidate.address)
	# add votes
	candidate.votes += 1
	candidate.election.voters += f"{matric_no} "
	db.session.commit()
	election = candidate.election
	flash(message, "success")
	return redirect(election.get_absolute_url)
	



@app.route('/about/')
def about():
	"""about"""
	return render_template('about.html')


