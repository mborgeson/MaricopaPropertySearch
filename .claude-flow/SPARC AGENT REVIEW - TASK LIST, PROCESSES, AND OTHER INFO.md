EXISTING PROJECT - ISSUE RESOLUTION GOALS:
First Goal: Convert all paths and references from windows path formatting to wsl/Linux path formatting. I copied the project from a windows folder to a ubuntu/Linux folder and now, not only are the references still corresponding to the previous project directory, all of the paths are in windows path formatting.

Second Goal: Please identify the various project scripts, determine the function/nature of each script, and then group the scripts by their function/nature (e.g., two different scripts that both were used to launch a dashboard would be grouped together as dashboard launcher scripts). Once all project scripts have been accounted for and placed into a like-kind group, then I will need a list to be generated enumerating the scripts in each group and their absolute path.
	• Next, each group list will be reviewed for a second time to determine the most complete, best performing, and highest overall quality script from that group, in regard to performing its function/task. Even after the optimal script is determined, there needs to be one final review of the other scripts in the same group to see if any of the functionality in those scripts could be utilized somewhere within the optimal script's code. Finally, after all of the best code has been incorporated into a single script, then the remaining deprecated scripts will be deleted, leaving a SINGLE & AUTHORTATIVE script/file for each component of the project (i.e., This aligns with the "DRY" method -- "DRY" is a coding principle meaning "Don't Repeat Yourself," advocating for the removal of duplicate code and information by abstracting it into a single, authoritative source. This promotes more maintainable, readable, and less error-prone code, as changes need only be made in one place).
	
Third Goal: Review the project directory, identify the various working scripts/files for each component of the project, especially each project component that is an integral component of the interactive GUI's functionality, understand the mechanics of why each of those correctly working files associated with disparate project components are working correctly, review the interactive GUI, test every component, element, attribute, and function within the interactive GUI to determine if working, thoroughly review those items not working and establish fixes for each of them, re-test the entire GUI at the end to ensure everything is working correctly, review the GUI for performance increases and optimizations, review the GUI for aesthetic improvements, review the GUI for any/all other recommendations you believe would enhance the interactive GUI and the project in general, and at the very end, make sure to thoroughly document the revisions made, as well as an entire redrafting of the project documentation to provide a step-by-step summarization of the comprehensive project.

Fourth Goal: After completing the above goals, please re-review the project to thoroughly update all of the documentation for the updated attributes across the project directory, remove any files/scripts that are no longer used in the project, are duplicative to the another file in the project, and/or are of very limited additional value to the project, ensure all final/authoritative files/scripts have the correct and updated dependency mappings and files/script references, and finally provide a list of recommendations to enhance the project any/all places that you identify as improvable.

Workflow Process and Structure:
	A. Agentic Workflow:
		a. For this Task/process I want to utilize a heavy agentic component to ensure this task is tackled by a team with specialists and will be a able to parallel process certain aspects of the this request as they first create a plan for their workflow. Further, I would like to utilize the Claude-Flow SPARC Agent Swarm, with parallel execution, batch processing, optimal agent orchestration, a maximum number of agents up to 12, the swarm "strategy" being automatically determined throughout the project as progress is made, and the swarm coordination "mode" should be determined by Claude-Flow based upon its understanding of the issues to resolve and its overall understanding of the project.
		b. Please review the Claude-Flow SPARC Agent Swarm Template to understand the questions being asked, and then utilize the insight gained from my "Issue Resolution Goals" for this project, which are listed above, to accurately and optimally complete the template questions.
			i. The template is at the following path - "/home/mattb/MaricopaPropertySearch/.claude-flow/Claude-Flow SPARC Agent Swarm Prompt.md".
	B. Memory, Session, and Conversation Checkpoint Process:
		a. The process documentation is included in the project file path as follows - "/home/mattb/MaricopaPropertySearch/Checkpoints/README.md"

Commands and Scripts:
	a. Manual Checkpoint Commands (Bash):
		a. The path to the documentation and reference to these commands is as follows - "/home/mattb/MaricopaPropertySearch/scripts/checkpoint_commands.sh"
		b. Primary Command Usage:
			a. Generate new checkpoint immediately - "./scripts/checkpoint_commands.sh generate"
			b. View latest checkpoint - "./scripts/checkpoint_commands.sh view"
			c. List all checkpoints (newest first) - "./scripts/checkpoint_commands.sh list"
			d. Test checkpoint generation - "./scripts/checkpoint_commands.sh test"
			e. Setup daily automatic generation - "./scripts/checkpoint_commands.sh setup-daily"
	b. Manual Checkpoint Commands (Python):
		a. The path to the documentation and reference to these commands is as follows - "/home/mattb/MaricopaPropertySearch/scripts/checkpoint_commands.sh"
		b. Primary Command Usage:
			a. python3 scripts/generate_checkpoint.py manual
			b. python3 scripts/generate_checkpoint.py git-commit
			c. python3 scripts/generate_checkpoint.py daily
			d. python3 scripts/generate_checkpoint.py test
		
	
Additionally, please see below for a list of document paths and general information that will help your issue resolution process:
	A. Document Paths:
		a. Previous Claude Conversations over This Project: "Project Documentation - MaricopaPropertySearch Previous Conversations.txt";
		b. Maricopa County Website URL List: "Project Documentation - Source URLS.txt";
		c. Maricopa County Assessor API Usage Details: "Project Documentation - API Usage Details.txt"; and
		d. Maricopa County Assessor Official API Documentation: "Project Documentation - MC Assessor API Documentation.pdf".
	B. General Information:
		a. Project Root Directory Path: "/home/mattb/MaricopaPropertySearch";
		b. There are various files/scripts throughout the project directory in the various folders. As such, this project review and initial understanding needs to be an important component of the process in order to understand the general structure, and identify all of the project component files;
		c. As there substantially too many files, creating technical debt", please make sure to ask me any questions about the project structure, codebase, etc. as you are starting the review and analysis process of the project. I want to make sure you use the correct information at the start, versus reading old documentation and relying on the information and references there; and
Maricopa County Assessor API Token:ca1a11a6-adc4-4e0c-a584-36cbb6eb35e5.