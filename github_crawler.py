import os
import requests
import pandas as pd
import threading
from flask import Flask, json, request, Response, render_template
from dotenv import load_dotenv
load_dotenv()
import itertools


class Crawler(object):
    def __init__(self):
        self.root = None
        self.count = {}
        self.count["open_issues_total"] = 0
        self.count["open_issues_24hr"] = 0
        self.count["open_issues_24hr_7days"] = 0
        self.count["open_issues_gt_7days"] = 0
        self.processed=False
        self.error = None
        
    def results(self):
        result = {}
        result["url"] = self.root
        result["counts"] = self.count
        result["processed"] = self.processed
        result["error"] = self.error
        return result

    def request(self):
        try:
            page_no = 1
            now = pd.datetime.now()
            open_issues_24hr =  now - pd.Timedelta('24H')
            open_issues_7days = now - pd.Timedelta('7D')
            header_content = {"User-Agent":os.environ.get("account"),
                             "Accept": "application/vnd.github.v3+json",
                             "Authorization":"token "+os.environ.get("token")}
            while (not self.processed) and (self.error == None):
                #Wait for some time before raising Timeout exception
                url = "https://api.github.com/repos/"+self.root+'/issues?&is=issue&state=open&per_page=100&page='+str(page_no)
                print (url)
                page = requests.get(url, headers=header_content)
                response = json.loads(page.text or page.content)
                if (page.ok):
                    this_df = pd.DataFrame.from_dict(response)
                    this_df["created_at"] = pd.to_datetime(this_df["created_at"])
                    if "pull_request" in this_df.columns:
                        this_df = this_df[this_df["pull_request"].isnull()]
                    self.count["open_issues_total"] += len(this_df)
                    self.count["open_issues_24hr"] += len(this_df[this_df["created_at"] >= open_issues_24hr])
                    self.count["open_issues_24hr_7days"] += len(this_df[(this_df["created_at"] < open_issues_24hr) & (this_df["created_at"] >= open_issues_7days)])
                    self.count["open_issues_gt_7days"] += len(this_df[this_df["created_at"] < open_issues_7days])
                    if (len(response) == 100):
                        page_no += 1  
                    else:
                        print ("Process complete")
                        self.processed = True
                        yield "data: %s\n\n" % (json.dumps(self.results())) 
                else:
                    self.processed = False
                    self.error = response["message"]
                    yield "data: %s\n\n" % (json.dumps(self.results())) 
            yield "Success"   
                    
        except requests.exceptions.ConnectionError as e:
            self.processed = False
            self.error = str(e)
            print ("Ignoring "+ str(self.root) +", URL might be incorrect") 
        except requests.exceptions.Timeout as e:
            self.processed = False
            self.error = str(e)
            print ("Ignoring "+ str(self.root) +", timeout error")
        except requests.exceptions.RequestException as e:
            self.processed = False
            self.error = str(e)
            print ("Ignoring: "+ str(self.root) +", " + e)
        except RuntimeError as e:
            self.processed = False
            self.error = str(e)
            print (e)
        finally:
            yield "data: %s\n\n" % (json.dumps(self.results()))
           
    

app = Flask(__name__)

@app.route('/show_results', methods = ['GET'])
def crawl_repo():
    repo_url = request.args.get('repo_url', default = None, type = str)
    if repo_url:
        cr = Crawler()
        cr.root = repo_url
        if request.headers.get('accept') == 'text/event-stream':
            print ("Requested")
            return Response(cr.request(), content_type='text/event-stream')
    
@app.route('/', methods = ['GET'])
def hello():
    return render_template("home.html")
    

if __name__ == '__main__':
    app.run(threaded=True)

