# git_crawler
Crawl public git repositories for open issues

App is hosted in Heroku : https://github-api-assignment.herokuapp.com/

Input: 
User can input a link to any public GitHub repository

Output:
Your UI should display a table with the following information -

- Total number of open issues 
- Number of open issues that were opened in the last 24 hours 
- Number of open issues that were opened more than 24 hours ago but less than 7 days ago 
- Number of open issues that were opened more than 7 days ago

Technology Stack:
- Front End - HTML, JavaScript, jQuery, CSS, AJAX
- Back End - Python (Flask - Server Sent Events, Gunicorn)

Solution Approach:

- Webpage takes the respository name in the owner/repo format. Eg. azure/azure-cli as Input
- Upon clicking the Search button:
   - Front End: If there is no EventSource configured, an event source is created to stream results from the Python API "/show_results". If all the results of the given repo is extracted or When there is an error. Client will request to close the stream.
   - Back End: If the request is of type "event-stream", initiate the EventStream which scans the repo for open issues. GitHub limits the number of results returned by an API to 100. So by subsequent queries, complete list of issues are retrieved.
   By default, querying issues will return pull requests also. This has been excluded from the results. Whenever result is obtained, it is emitted to the Client, until the Client explicitly wants to close the EventStream.
   
   
Further Enhancements:



