# INFORMATION ------------------------------------------------------------------------------------------------------- #


# Author:  Steven Spratley, extending code by Guang Ho and Michelle Blom
# Date:    12/02/23
# Purpose: Defines a general game runner for the COMP90054 competitive game environment
# Notes:   This port is incomplete, and will req


# IMPORTS ------------------------------------------------------------------------------------------------------------#


from re import L
import sys
import os
import importlib
import traceback
import datetime
import time
import pickle
import random
import git
import shutil
import pytz
import json
from template import Agent as DummyAgent
from game import Game, GameReplayer
from optparse import OptionParser


# CONSTANTS ----------------------------------------------------------------------------------------------------------#


# team_indexs   = ["red_team","blue_team"]
DEFAULT_AGENT = "agents.generic.random"
DEFAULT_AGENT_NAME = "default"
# NUM_AGENTS    = 2

TIMEZONE = pytz.timezone('Australia/Melbourne')
DATE_FORMAT = '%d/%m/%Y %H:%M:%S'  # RMIT Uni (Australia)


# CLASS DEF ----------------------------------------------------------------------------------------------------------#


def is_git_repo(path):
    try:
        _ = git.Repo(path).git_dir
        return True
    except git.InvalidGitRepositoryError:
        return False

# Extract the timestamp for a given tag in a repo
def get_commit_time(repo:git.Repo):
    """
    Returns the commit time based on the TIMEZONE

    :param repo: the repository 
    :return: the commit time
    """
    commit = repo.commit()
    commit_date = datetime.datetime.fromtimestamp(commit.committed_date, tz=TIMEZONE)
    return commit_date.strftime(DATE_FORMAT)

def gitCloneTeam(team_info, output_path,default_branch='main',token_path=""):
    if not os.path.exists(output_path):
        os.makedirs(output_path)   
    token = None
    with open(token_path, "r") as f:
        token = f.read()
    # clone_url = f"git@github.com:{team_info['url'].replace('https://github.com/','')}"
    clone_url = f"https://{token}@{team_info['url'].replace('https://','')}"
    team_name = str(team_info['team_name'])
    repo_path = f"{output_path}/{str(team_info['team_name'])}"
    commit_id = team_info['commit_id']
    submission_time='N/A'
    if not os.path.exists(repo_path):
        os.makedirs(repo_path)

    if not is_git_repo(repo_path):
        try:
            repo = git.Repo.clone_from(clone_url, repo_path, branch=default_branch, no_checkout=True)
            repo.git.checkout(commit_id)
            # repo = git.Repo.clone_from(clone_url, repo_path)
            submission_time = get_commit_time(repo)
            team_info.update({'git_status': True})
            team_info.update({'comments':'N/A'})
            team_info.update({'submitted_time': submission_time})
            repo.close()
            # teams_new.append(team_name)
        except git.GitCommandError as e:
            # teams_missing.append(team_name)
            print(f'Repo for team {team_name} with tag/branch "{default_branch}" cannot be cloned: {e.stderr}')

            team_info.update({'git_status':False})
            team_info.update({'comments':f'Repo for team {team_name} with tag/branch {default_branch} cannot be cloned: {e.stderr}'})
            # repo.close()
        except KeyboardInterrupt:
            print('Script terminated via Keyboard Interrupt; finishing...')
            sys.exit("keyboard interrupted!")
            # repo.close()
        except TypeError as e:
            print(f'Repo for team {team_name} was cloned but has no tag {default_branch}, removing it...: {e}')
            shutil.rmtree(repo_path)
            # teams_notag.append(team_name)
            team_info.update({'git_status':False})
            team_info.update({'comments':f'Repo for team {team_name} was cloned but has no tag {default_branch}, removing it...: {e}'})
            # repo.close()
        except Exception as e:
            print(
                f'Repo for team {team_name} cloned but unknown error when getting tag {default_branch}; should not happen. Stopping... {e}')
            team_info.update({'git_status':False})
            team_info.update({'comments':f'Repo for team {team_name} cloned but unknown error when getting tag {default_branch}; should not happen. Stopping... {e}'})
            # repo.close()  
    else:
        team_info.update({'git_status':True})

    if team_info['git_status']:
        try:
            if not os.path.exists(f"agents/{team_name}"):
                shutil.copytree(f"{repo_path}/agents/{team_name}", f"agents/{team_name}")
        except:
            traceback.print_exc()
        shutil.rmtree(f"{repo_path}")
    team_info.update({'copy_files':os.path.exists(f"agents/{team_name}/myTeam.py")})
    return team_info



def run(options,msg):
    num_of_agents = options.num_of_agents

    # fill in the defaults
    agent_names = options.agent_names.split(",")
    agents = options.agents.split(",")
    agent_urls = options.agent_urls.split(",")
    agent_commit_ids = options.agent_commit_ids.split(",")


    missing  = num_of_agents-len(agent_names)
    for i in range(missing):
        agent_names.append(DEFAULT_AGENT_NAME)
    missing  = num_of_agents-len(agents)
    for i in range(missing):
        agents.append(DEFAULT_AGENT)


    clone_result = dict()
    clone_result['teams'] = dict()
    # load agents info
    for i in range(len(agent_urls)):
        team_info = {}
        team_info['team_name'] = agent_names[i]
        team_info['agent'] = agents[i]

        team_info['url'] = agent_urls[i]
        team_info['commit_id'] = agent_commit_ids[i]
        clone_info = gitCloneTeam(team_info, output_path="temp",default_branch=options.default_branch,token_path = options.token_path)
        team_info.update(clone_info)
        clone_result['teams'].update({i:team_info})

    with open('output/team_info.json', 'w') as f:
        json.dump(clone_result,f)



def loadParameter():

    """
    Processes the command used to run Yinsh from the command line.
    """
    usageStr = """
    USAGE:      python runner.py <options>
    EXAMPLES:   (1) python runner.py
                    - starts a game with four random agents.
                (2) python runner.py -c MyAgent
                    - starts a fully automated game where Citrine team is a custom agent and the rest are random.
    """
    parser = OptionParser(usageStr)
    parser.add_option('-a','--agents', help='A list of the agents, etc, agents.myteam.player', default="agents.TheLastSplendorBender.random,agents.gm-onyx.random") 
    parser.add_option('-n', '--num_of_agents', type='int',help='The number of agents in this game', default=2)
    parser.add_option('--token_path', help='the path to token', default="main") 
        
    parser.add_option('--default_branch', help='the default branch name', default="main") 
    parser.add_option('--agent_names', help='A list of agent names', default="TheLastSplendorBender,gm-onyx") 

    parser.add_option('--agent_urls', help='A list of urls', default="https://github.com/COMP90054-2021S2/contest-thelastsplendorbender.git,https://github.com/COMP90054-2021S2/contest-gm-onyx.git")
    parser.add_option('--agent_commit_ids', help='A list of commit ids', default="7faeecbefb71af2d9bd4b4c043840e567d7bb58a,3bd11a23e003b416e11831d57c417d0fc5a4f957") 

    options, otherjunk = parser.parse_args(sys.argv[1:] )
    assert len(otherjunk) == 0, "Unrecognized options: " + str(otherjunk)

    return options


# MAIN ---------------------------------------------------------------------------------------------------------------#


if __name__ == '__main__':

    """
    The main function called when advance_model.py is run
    from the command line:

    > python runner.py

    See the usage string for more details.

    > python runner.py --help
    """
    msg = ""
    options = loadParameter()
    run(options,msg)



# END FILE -----------------------------------------------------------------------------------------------------------#

# python3 general_game_runner.py -t --cloud -a agents.group6.player,agents.group6.player --agent_urls 'https://github.com/COMP90054-2022S1/comp90054-yinsh-project-group6','https://github.com/COMP90054-2022S1/comp90054-yinsh-project-group6' --agent_commit_ids "c2dfa5a2cc4aa4672ed5b6c4979fdb451265f9b8","c2dfa5a2cc4aa4672ed5b6c4979fdb451265f9b8" --agent_names group6,group6 -s -l