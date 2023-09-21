### cordofind

# How to run

0. *Change or delete environment prefix in `environment.yml`
1. `conda env create -f environment.yml`
2. `conda activate cordofind`
3. `python3 main.py [artist names]`

\* I think? Shouldn't be my laptop directory path at least

# For longer running processes
1. Start process using the above command
2. Run the command `ps | grep python`
3. Copy the pid of the process running cordofind
4. Run `caffeinate -i -s -w [pid]`, so your Mac does not sleep until the process finishes

# How to export environment
`conda env export > environment.yml`

# How to use data [In Progress]
Upload to AirTable
