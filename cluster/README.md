# Running a Flask App Interactively on Mahti (CSC)

This guide explains how to launch a Flask app on a Mahti compute node using an interactive Slurm job and access it locally through SSH port forwarding.

---

## Overview

Because compute nodes are not directly reachable from your laptop, we use:

```
Laptop → SSH tunnel → Mahti login node → compute node → Flask app
```

Key requirements:

* Run Flask inside an interactive Slurm job
* Bind Flask to `0.0.0.0` (not 127.0.0.1)
* Forward the compute-node port through the login node

---

## Step 1 — Start Interactive Job

SSH to Mahti normally:

```bash
ssh <username>@mahti.csc.fi
```

Start an interactive GPU job:

```bash
srun --interactive \
  --partition gputest \
  --ntasks=1 \
  --nodes=1 \
  --gres=gpu:a100:1 \
  --account=project_2017554 \
  --time=00:15:00 \
  --pty bash
```

You are now on a compute node.

Check which one:

```bash
hostname
```

Example output:

```
g1101
```

Save this; you’ll need it for port forwarding.

---

## Step 2 — Launch Flask App on Compute Node

Go to your project directory:

```bash
cd /scratch/project_2017554/dir
source venv/bin/activate #You need to have created this virtual environment beforehand
```

Set environment variables:

```bash
export FLASK_APP=joker.py # Insert here the name of your app
export FLASK_DEBUG=1
```

Start Flask:

```bash
flask run --host 0.0.0.0 --port 8000
```

Important:

* `--host 0.0.0.0` allows access from outside the compute node
* The command will “hang” — this is normal (server is running)

---

## Step 3 — Create SSH Tunnel from Laptop

Open a **new terminal on your laptop** and run:

```bash
ssh -L 8000:g1101:8000 <username>@mahti.csc.fi
```

Replace `g1101` with your compute node hostname.

---

## Step 4 — Open in Browser

On your laptop:

```
http://localhost:8000
```

Your Flask app should now load.

---

## Notes

* Do **not** run web servers on login nodes
* Always use interactive Slurm jobs
* Use short time limits for demos
* Choose unused ports (8000, 8080, 5000, etc.)