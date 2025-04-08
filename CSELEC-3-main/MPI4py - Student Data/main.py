# dependencies
"""
!pip install mpi4py
!nvcc --version
!nvidia-smi
"""
import pandas as pd
import numpy as np
import multiprocessing as mp
import random
import os
import getpass

# file import
from google.colab import files
import pandas as md

uploaded = files.upload()

filename = list(uploaded.keys())[0]
df = pd.read_csv(filename)

df.head()

# Main Code
from mpi4py import MPI
import pandas as pd
import time

### SEQUENTIAL CODE ####################################################################################################
# read CSV file
start_read_time_sequential = time.time()
df = pd.read_csv("synthetic_student_data.csv")
end_read_time_sequential = time.time()
print(f"CSV Read Time Sequential: {end_read_time_sequential - start_read_time_sequential:.4f} seconds")

#Get Unique department names
departments = df["Department"].unique()

#Compute average GPA per department
def compute_avg_gpa_seq(dept):
  sub_df = df[df["Department"] == dept]
  return dept, sub_df["GPA"].mean()

start_time = time.time()

# Execute sequential
results = [compute_avg_gpa_seq(dept) for dept in departments]
avg_gpa = dict(results)

end_time = time.time()

# Print Execution Time
print(f"Sequential Execution Time: {end_time - start_time:.4f} seconds\n")


### PARALLEL CODE #######################################################################################################
# Initialize MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()   # Process ID
size = comm.Get_size()   # Total processes

# Start measuring time (only in root process)
if rank == 0:
    total_start_time = time.time()

# Root process reads the CSV and distributes data
df = None
departments = None

if rank == 0:
    start_read_time_parallel = time.time()
    df = pd.read_csv("synthetic_student_data.csv")  # Load dataset
    end_read_time_parallel = time.time()
    print(f"CSV Read Time Parallel: {end_read_time_parallel - start_read_time_parallel:.4f} seconds")

    departments = df["Department"].unique()
    

# Broadcast the full dataset and department list to all processes
df = comm.bcast(df, root=0)
departments = comm.bcast(departments, root=0)

# Distribute departments among available processes
chunk_size = len(departments) // size
start = rank * chunk_size
end = start + chunk_size if rank != size - 1 else len(departments)
assigned_departments = departments[start:end]

# Function to compute average GPA
def compute_avg_gpa(dept):
    sub_df = df[df["Department"] == dept]
    student_count = len(sub_df)  # Count students
    avg_gpa = sub_df["GPA"].mean()
    return dept, (student_count, avg_gpa)  # Return tuple (student count, GPA)


# Each process computes GPA for its assigned departments
local_start_time = time.time()
local_results = {dept: compute_avg_gpa(dept)[1] for dept in assigned_departments}
local_end_time = time.time()
local_processing_time = local_end_time - local_start_time

# Gather results at root process
all_results = comm.gather(local_results, root=0)

# Measure final time (only in root process)
if rank == 0:
    total_end_time = time.time()

    # Combine results from all processes
    final_gpa_per_department = {}
    for result in all_results:
        if result:
            final_gpa_per_department.update(result)

    # Display execution time
    print(f"MPI Parallel Execution Time: {total_end_time - total_start_time:.4f} seconds")

    # Display Speedup
    speedup = (end_time - start_time) / (total_end_time - total_start_time)
    print(f"\nSpeedup: {speedup:.4f}x")

    # Display Efficiency
    print(f"Efficiency: {(speedup / size) * 100:.2f}%")

    # Display computed GPA by department
    print("\nComputed Data per Department: ")
    print("{:<20}{:<15}{:<10}".format("Department", "Student Count", "Average GPA"))
    print("================================================")
    for dept, (student_count, avg_gpa) in final_gpa_per_department.items():
      print(f"{dept:<20}{student_count:<15}{avg_gpa:<5.2f}")

# Print each process's local execution time
print(f"\nProcess {rank} Local Computation Time: {local_processing_time:.4f} seconds")
