# radial-bracket
Create radial bracket images from JSON input files listing the teams and matches of the tournament.  

# Prerequisites
Requires Python3 with Pillow module 

# Usage
Create a tournament JSON file or modify tournaments/ccl2022.json with game details.  Add team logos to the logos folder and team 
details to teams.json. Run main.py and specify the tournament file with the -t option.    
   
    python3 main.py -t ccl2022

Games in the tournament JSON file are numbered from the final outwards, starting with 1.  See examples/game-numbers.png for details.
