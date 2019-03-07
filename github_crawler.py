import os
import requests
import pandas as pd
import datetime
import threading
from flask import Flask, json, request, Response, render_template, jsonify
from dotenv import load_dotenv
load_dotenv() #Load the environmental variables if present in the .env file


class Crawler(object):
    def __init__(self, url):
        self.root = url # URL to crawl
        self.count = {}  # The counts of issues are stored as a dictionary, initialised with 0
        self.count["open_issues_total"] = 0
        self.count["open_issues_24hr"] = 0
        self.count["open_issues_24hr_7days"] = 0
        self.count["open_issues_gt_7days"] = 0
        self.error = None # Error message if present
        
    def prepare_results(self):
        #Send the crawler object information as result to the front-end
        result = {}
        result["url"] = self.root
        result["counts"] = self.count
        result["error"] = self.error
        return result

    def request(self):
        try:
            #Get current time as now
            now = datetime.datetime.now().replace(microsecond=0)
            #Find time which is 24 hrs ago from now
            open_issues_24hr_time =  (now - datetime.timedelta(hours=24)).isoformat()
            #Find time which is 7 days ago from now
            open_issues_7days_time = (now - datetime.timedelta(days=7)).isoformat()
            #Initialise appropriate request header contents
            header_content = {
                "User-Agent":os.environ.get("account"), #GitHub account name
                "Accept": "application/vnd.github.v3+json",
                "Authorization":"token "+os.environ.get("token") #Oauth token after registering the application in GitHub
            }

            #Extract the total open issue count for the repo
            repo_summary_url = "https://api.github.com/search/issues?q=state:open+is:issue+repo:" + self.root
            repo_summary_response = requests.get(repo_summary_url, headers=header_content)
            repo_summary = json.loads(repo_summary_response.text or repo_summary_response.content)
            if repo_summary_response.status_code == 422:
                # A 422 unauthorised is handled
                self.error = repo_summary["errors"][0]["message"]
                return jsonify(self.prepare_results())

            #If the response of the page is 200 OK, extract the data
            if (repo_summary_response.ok):
                #Extract the total count
                self.count["open_issues_total"] = repo_summary["total_count"]
                
            #Extract the total open issue count created 24hrs ago
            open_issues_24hr_url = "https://api.github.com/search/issues?q=state:open+is:issue+repo:" + self.root+ "+created:>=" + open_issues_24hr_time+"-05:30"
            open_issues_24hr_response = requests.get(open_issues_24hr_url, headers=header_content)
            open_issues_24hr = json.loads(open_issues_24hr_response.text or open_issues_24hr_response.content)

            #If the response of the page is 200 OK, extract the data
            if (open_issues_24hr_response.ok):
                #Extract the total count
                self.count["open_issues_24hr"] = open_issues_24hr["total_count"]

            #Extract the total open issue count created between 24hrs to 7 days
            open_issues_24hr_7days_url = "https://api.github.com/search/issues?q=state:open+is:issue+repo:" + self.root+ "+created:" + open_issues_7days_time+"-05:30.."+open_issues_24hr_time+"-05:30"
            open_issues_24hr_7days_response = requests.get(open_issues_24hr_7days_url, headers=header_content)
            open_issues_24hr_7days = json.loads(open_issues_24hr_7days_response.text or open_issues_24hr_7days_response.content)

            #If the response of the page is 200 OK, extract the data
            if (open_issues_24hr_7days_response.ok):
                #Extract the total count
                self.count["open_issues_24hr_7days"] = open_issues_24hr_7days["total_count"]

            #Total open issue count created 7 days ago = total open issue - open issues created within 24 hrs - open issues created betwen 24 hrs & 7 days
            self.count["open_issues_gt_7days"] = self.count["open_issues_total"] - self.count["open_issues_24hr_7days"] - self.count["open_issues_24hr"]
            return jsonify(self.prepare_results())
                 
        except requests.exceptions.ConnectionError as e:
            #Exception due to Connection Error, set the appropriate error message
            self.error = str(e)
            print ("Ignoring "+ str(self.root) +", URL might be incorrect") 
        except requests.exceptions.Timeout as e:
            #Exception due to Timeout Error, set the appropriate error message
            self.error = str(e)
            print ("Ignoring "+ str(self.root) +", timeout error")
        except requests.exceptions.RequestException as e:
            #Exception due to Request Exeception, set the appropriate error message
            self.error = str(e)
            print ("Ignoring: "+ str(self.root) +", " + e)
        finally:
            #Return the intermediate results
            return jsonify(self.prepare_results())
        
           
#Create the Flask server object
app = Flask(__name__)

#API which displays the results in the form of event-stream
@app.route('/show_results', methods = ['GET'])
def crawl_repo():
    #Get the repo_url query parameter
    repo_url = request.args.get('repo_url', default = None, type = str)
    if repo_url:
        #Create the crawler object with the url and initiate the request
        cr = Crawler(repo_url.strip("/"))
        return cr.request()

#Route for the home page
@app.route('/', methods = ['GET'])
def hello():
    return render_template("home.html")

if __name__ == '__main__':
    app.run(threaded=True)

