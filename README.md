# git_crawler
Crawl public git repositories for open issues

App is hosted in Heroku : https://github-api-assignment.herokuapp.com/

Input: 
User can input a link to any public GitHub repository in owner/repo format. Eg. azure/azure-cli

Output:
Your UI should display a table with the following information -

- Total number of open issues 
- Number of open issues that were opened in the last 24 hours 
- Number of open issues that were opened more than 24 hours ago but less than 7 days ago 
- Number of open issues that were opened more than 7 days ago

Technology Stack:
- Front End - HTML, JavaScript, jQuery, CSS, AJAX
- Back End - Python (Flask REST API, Gunicorn)

Solution Approach:

- Webpage takes the repository name in the owner/repo format. Eg. azure/azure-cli as Input
- Upon clicking the Search button:
   - Front End: An AJAX request is sent to the Python API "/show_results". When there is any error in server / error in retrieving repo details, appropriate error messages as displayed.
   - Back End: When the request from the client is received, issue 3 GitHub Search API hits which finds the total open issues, open issues created within 24 hours, open issues created between 24 hrs and 7 days, respectively. When all the 3 results are obtained, remaining value i.e. open issues created more than 7 days ago can be calculated as follows:
   - 7days_ago = # total - # 24hrs - # between 24hrs and 7 days    
   
Further Enhancements:
- When a user clicks Search, Spinner can be displayed over content. The user will then be able to understand easily that data is being loaded

- While typing the input, suggestions could be provided. For eg. Whenever the user is typing the owner, possible owner names can be listed. Similarly for the repo name after the user typed owner name. Also when the user entered an incorrect repo URL, suggestions can be displayed.

- Error messages could be displayed in Toast instead of Browser pop-ups.


