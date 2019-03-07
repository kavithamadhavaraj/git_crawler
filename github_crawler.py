import os
import requests
import pandas as pd
import threading
from flask import Flask, json, request, Response, render_template
from dotenv import load_dotenv
load_dotenv() #Load the environmental variables if present in the .env file

class Crawler(object):
    def __init__(self):
        self.root = None # URL to crawl
        self.count = {}  # The counts of issues are stored as a dictionary, initialised with 0
        self.count["open_issues_total"] = 0
        self.count["open_issues_24hr"] = 0
        self.count["open_issues_24hr_7days"] = 0
        self.count["open_issues_gt_7days"] = 0
        self.processed=False # Signal to indicate if the crawler finished processing all pages of the given repo
        self.error = None # Error message if present
        
    def send_results(self):
        #Send the crawler object information as result to the front-end
        result = {}
        result["url"] = self.root
        result["counts"] = self.count
        result["processed"] = self.processed
        result["error"] = self.error
        return result

    def request(self):
        try:
            #First hit to the GitHub API should have page no as 1
            page_no = 1
            #Get current time as now
            now = pd.datetime.now()
            #Find time which is 24 hrs ago from now
            open_issues_24hr =  now - pd.Timedelta('24H')
            #Find time which is 7 days ago from now
            open_issues_7days = now - pd.Timedelta('7D')
            #Initialise appropriate request header contents
            header_content = {
                "User-Agent":os.environ.get("account"), #GitHub account name
                "Accept": "application/vnd.github.v3+json",
                "Authorization":"token "+os.environ.get("token") #Oauth token after registering the application in GitHub
            }
            #Until all the pages of the repo is processed or until any error is occurred, do the following
            while (not self.processed) and (self.error == None):
                #Search for the issues in the url specified by user with the following attributes
                #Type: Issue
                #State : Open
                #Number of entries to retrieve : 100 entries maximum (limited by GitHub)
                #Page :  Page to retrieve
                url = "https://api.github.com/repos/"+self.root+'/issues?&is=issue&state=open&per_page=100&page='+str(page_no)
                print (url)
                #Hit the API
                page = requests.get(url, headers=header_content)
                #Extract the response
                response = json.loads(page.text or page.content)
                #If the response of the page is 200 OK, extract the data
                if (page.ok):
                    #Convert the response data to dataframe
                    this_df = pd.DataFrame.from_dict(response)
                    #Format the date attribute for further filtering
                    this_df["created_at"] = pd.to_datetime(this_df["created_at"])
                    #Ignore pull requests from the response
                    if "pull_request" in this_df.columns:
                        this_df = this_df[this_df["pull_request"].isnull()]
                    #Extract the count of total open issues
                    self.count["open_issues_total"] += len(this_df)
                    #Extract the count of open issues created within 24 hours
                    self.count["open_issues_24hr"] += len(this_df[this_df["created_at"] >= open_issues_24hr])
                    #Extract the count of open issues created between 24 hours and 7 days
                    self.count["open_issues_24hr_7days"] += len(this_df[(this_df["created_at"] < open_issues_24hr) & (this_df["created_at"] >= open_issues_7days)])
                    #Extract the count of open issues created 7 days ago
                    self.count["open_issues_gt_7days"] += len(this_df[this_df["created_at"] < open_issues_7days])
                    #If the retrieved issue count is 100, then there is possibility of next page
                    if (len(response) == 100):
                        page_no += 1  
                    else:
                        #Mark the process as complete
                        print ("Process complete")
                        self.processed = True
                    #Return the intermediate results
                    yield "data: %s\n\n" % (json.dumps(self.send_results())) 
                else:
                    #Error in retrieving the page, set the error message and stop the processing.
                    self.processed = False
                    self.error = response["message"]
                    #Return the intermediate results
                    yield "data: %s\n\n" % (json.dumps(self.send_results())) 
                    
        except requests.exceptions.ConnectionError as e:
            #Exception due to Connection Error, set the appropriate error message
            self.processed = False
            self.error = str(e)
            print ("Ignoring "+ str(self.root) +", URL might be incorrect") 
        except requests.exceptions.Timeout as e:
            #Exception due to Timeout Error, set the appropriate error message
            self.processed = False
            self.error = str(e)
            print ("Ignoring "+ str(self.root) +", timeout error")
        except requests.exceptions.RequestException as e:
            #Exception due to Request Exeception, set the appropriate error message
            self.processed = False
            self.error = str(e)
            print ("Ignoring: "+ str(self.root) +", " + e)
        finally:
            #Return the intermediate results
            yield "data: %s\n\n" % (json.dumps(self.send_results()))
           
#Create the Flask server object
app = Flask(__name__)

#API which displays the results in the form of event-stream
@app.route('/show_results', methods = ['GET'])
def crawl_repo():
    #Get the repo_url query parameter
    repo_url = request.args.get('repo_url', default = None, type = str)
    if repo_url:
        #Create the crawler object and assign the url as the root
        cr = Crawler()
        cr.root = repo_url
        #Initiate the event-stream if the request type is event-stream
        if request.headers.get('accept') == 'text/event-stream':
            print ("Requested")
            return Response(cr.request(), content_type='text/event-stream')

#Route for the home page
@app.route('/', methods = ['GET'])
def hello():
    return render_template("home.html")
    

if __name__ == '__main__':
    app.run(threaded=True)

