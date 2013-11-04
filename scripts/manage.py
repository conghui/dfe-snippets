"""Simple script to manage the creation and verification of projects."""
# TODO Update to work with projects that have maultiple maxcompiler implementations
# At the moment, the assumed dir structure is Concept/Implementation/*.*

import os
import re
import subprocess


from os.path import join


# Custom exception definitions
class LinterException(Exception):
    pass


# Some regular expresssion definitions useful for this module
DESIGN_FILE_RE = re.compile(r'.*\.(maxj|java)')
CPU_FILE_RE = re.compile(r'.*\.(cpp|c)')
MAKEFILE_RE = re.compile(r'Makefile')

START_COMMENT_RE = re.compile(r'(\s)*/\*\*\*') # start comments with /***
END_COMMENT_RE = re.compile(r'(\s)*\*/') # end comments with */

GIT_BRANCH = re.compile(r'\* .*')
PROJECT_RE = re.compile(r'(?P<concept>.*)/(?P<project>.*)/src/.*')

# The project  directory (assumes this script lives in ROOT_DIR/scripts/)
ROOT_DIR = "../"


# Projects that should be excluded from linting / testing / post-processing
NON_PROJECT_DIRS = ['scripts', '.git', 'WISHLIST', 'Readme.md']


STARTING_COMMENT_MAP = {}

class WikiPage(object):
    
    def __init__(self, project, contents):
        self.project = project
        self.contents = contents

    def WriteToFile(self, wiki_path):
        f = open(os.path.join(wiki_path, self.project.name + '.md'), 'w')
        f.write(self.contents)
        f.close()


class Comment(object):
    
    def __init__(self, comment, snippet):
        self.comment = comment
        self.snippet = snippet

    def __str__(self):
        return 'Comment(c={}, s={})'.format(self.comment, self.snippet)


class Project(object):

    def __init__(self, concept, name, path, new=False):
        super(Project, self).__init__()
        self.concept = concept
        self.name = name
        self.path = path
        self.new = new
        self.starting_comments = {}
        self.in_line_comments = {}

    def GetFullPathRelativeToTopDir(self):
        return os.path.join(self.concept, self.name)

    def InterestingFile(path):
        return DESIGN_FILE_RE.match(path) or CPU_FILE_RE.match(path) or MAKEFILE_RE.match(path)

    def GetFiles(self):
        return os.listdir(self.path)

    def GetComments(self, file_name):
        abs_path = os.path.join(self.path, file_name)
        return ExtractCommentsFromFile(abs_path, self)

    def __str__(self):
        return 'Project(concept={}, name={}, path={}, files={})'.format(
            self.concept, self.name, self.path, [str(f) for f in self.GetFiles()])

    def __hash__(self):
        return hash(self.concept)

    def __eq__(self, other):
        return self.concept == other.concept and self.name == other.name


def ExtractCommentsFromFile(path, project):
    class State(object):
        NONE = 0
        PARSING_COMMENT = 1
        PARSING_SNIPPET = 2
        
    file = open(path)
    first = True
    first_comment = True
    parsed_code = False
    comment = ""
    snippet = ""

    s = State.NONE

    starting_comment = None
    in_line_comments = []

    for line in file.readlines():
        if s == State.PARSING_SNIPPET:
            if line.strip():
                snippet += line
                continue

            filename = os.path.basename(path)
            c = Comment(comment, snippet)
            if first_comment and not parsed_code:
                starting_comment = c
                first_comment = False
            else:
                in_line_comments.append(c)
            comment = ''
            snippet = ''
            s = State.NONE
        elif s == State.PARSING_COMMENT:
            if re.match(END_COMMENT_RE, line):
                s = State.PARSING_SNIPPET
                continue
            comment += line
        else:
            if re.match(START_COMMENT_RE, line):
                s = State.PARSING_COMMENT
            elif line.strip():
                parsed_code = True


    return starting_comment, in_line_comments


def ExtractCheckStatusBlock(path):
    return None

def LintJavaFile(path, project):
   ExtractComments(path, project)
   return start_comment

def LintCpuFile(path, project):
    ExtracOmments(path, projects)
    start_comment = ExtractStartingBlockComment(path, project)
    # TODO: checksReturnStatus = ExtractCheckStatusBlock(path)
    # return start_comment and checksReturnStatus
    return start_comment


def LintProjects(projects):
    # represents the number of linted files (Design, CPU, Makefile)
    stats = [0, 0, 0]
    for proj in projects:
        top_rel_path = proj.GetFullPathRelativeToTopDir()
        proj_path = os.path.join(ROOT_DIR, top_rel_path)
        print '\tLinting ' + top_rel_path
        for dirpath, dirnames, filenames in os.walk(proj_path):
            print '\t\tFiles ' + str(filenames)
            for filename in filenames:
                path = os.path.join(dirpath, filename)
                lint = True
                if DESIGN_FILE_RE.match(path):
                    lint = LintJavaFile(path, proj)
                    stats[0] += 1
                elif CPU_FILE_RE.match(path):
                    lint = LintCpuFile(path, proj)
                    stats[1] += 1
                if not lint:
                    print 'Linting file ' + path + ' failed'

    return stats


def GetProjectDirs():   
    return [d for d in os.listdir(ROOT_DIR) if d not in NON_PROJECT_DIRS]


def GetCurrentGitBranch():
    git_proc = subprocess.Popen(['git', 'branch'], stdout=subprocess.PIPE)

    current_git_branch = None
    while True:
        line = git_proc.stdout.readline()        
        if not line:
            break
        if GIT_BRANCH.match(line):
            current_git_branch = line[2:].strip()
            break
        
    return current_git_branch


def GetProjectName(filename):
    match = PROJECT_RE.match(filename)
    if match:
        return match.group('project')
    return None


def GetProjectConcept(filename):
    match = PROJECT_RE.match(filename)
    if match:
        return match.group('concept')
    return None
    

def LoadGitProjectData(git_process):

    modified_projs = set()
    new_projs = set()
    
    while True:
        line = git_process.stdout.readline()
        if not line: 
            break

        # git status returns ' M <file>', diff returns 'M <file>'
        line = line.strip() 
        change_type = line[0]

        line = line[2:].strip()
        project_name = GetProjectName(line)
        project_path = os.path.dirname(line)
        concept = GetProjectConcept(line)
        if project_name:
            if change_type == 'M':
                modified_projs.add(Project(concept, project_name, project_path))
            elif change_type == 'A':
                new_projs.add(Project(concept, project_name, project_path, True))

    return modified_projs, new_projs


def GetLocallyModifiedFiles():
    git_proc = subprocess.Popen(['git', 'status', '-s'], stdout=subprocess.PIPE)
    a, b =  LoadGitProjectData(git_proc)
    return a, b

    
def GetModifiedFilesInBranch(localGitBranch):
    """This assumes that the local branch is tracking the same named remote branch."""
    remote_branch = 'remotes/origin/' + localGitBranch
    git_proc = subprocess.Popen(['git', 'diff', '--name-status', 
                                remote_branch, localGitBranch, '--'], 
                               stdout=subprocess.PIPE)
    return LoadGitProjectData(git_proc)



def GetAllModifiedOrNewFiles(localGitBranch):
    # get changes committed locally that differ from remote branch
    modified_projs, new_projs = GetLocallyModifiedFiles()

    # get un-commited local changes
    local_modified_projs, local_new_projs = GetModifiedFilesInBranch(localGitBranch)

    
    return list(modified_projs | local_modified_projs), list(new_projs | local_new_projs)
    
        
def GetNewOrRecentlyModifiedProjects():
    current_git_branch = GetCurrentGitBranch()
    modified_projects = GetAllModifiedOrNewFiles(current_git_branch)
    return modified_projects


def RunTests(projects):
    pass


def GenerateWikiPage(project):
    contents = ""
    for f in project.GetFiles():
        comments = project.GetComments(f)
        if not comments[0]:
            continue
        contents += f + '\n====\n'
        contents += comments[0].comment.strip() + '\n'
        if comments[1]:
            contents += "##Snippets\n"
        for c in comments[1]:
            contents += c.comment.strip()+ '\n```\n'
            if c.snippet:
                contents += c.snippet
            contents += '```\n'
        contents += '\n'
    return WikiPage(project, contents)


def GenerateWikiPages(projects):
    wiki_pages = []
    for project in projects:
        wiki_pages.append(GenerateWikiPage(project))
    return wiki_pages


def main():
    # TODO: in the long term this should be an interactive shell based
    # program or at the very least take some command line args to
    # support selective: 
    #   1. linting
    #   2. testing
    #   3. comment extraction and updates
    #   4. new project creation

    modified_projs, new_projects = GetNewOrRecentlyModifiedProjects()
    changed_projects = new_projects + modified_projs
    print '1. Found {} new or recently modified projects:'.format(
        len(changed_projects))
    for proj in changed_projects:
        print '\t' + str(proj) + '\n'


    print '2. Linting all changed projects' 
#    lint_stats = LintProjects(changed_projects)
#    print '\tLinted {} Design file(s), {} CPU file(s) and {} Makefiles\n'.format(
#        lint_stats[0], lint_stats[1], lint_stats[2])


    print '3. Testing all changed projects\n'
    # TODO RunTests(changed_projects)

    print '4. Generating wiki page for changed projects ({})'.format(
       [str(s) for s in changed_projects])
    wiki_path = '../../maxdge-snippets-wiki'
    for page in GenerateWikiPages(changed_projects):
        page.WriteToFile(wiki_path)
#    GenerateContentsPage().WriteToFile(wiki_path)

if __name__ == "__main__":
    main()
