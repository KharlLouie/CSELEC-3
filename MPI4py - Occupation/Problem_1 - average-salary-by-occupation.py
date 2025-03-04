#   PROBLEM 1:
#   AVERAGE SALARY BY OCCUPATION

from mpi4py import MPI
import pandas as pd
import time
import matplotlib.pyplot as plt
import seaborn as sns

### SEQUENTIAL CODE ####################################################################################################
# Read CSV file
start_read_time_sequential = time.time()
df = pd.read_csv("ph_occupation_dataset.csv")
end_read_time_sequential = time.time()
print(f"CSV Read Time Sequential: {end_read_time_sequential - start_read_time_sequential:.4f} seconds")

# Get Unique Occupation names
occupations = df["Occupation"].unique()

# Compute average Salary per occupation
def compute_avg_salary_sequential(occupation):
    sub_df = df[df["Occupation"] == occupation]
    return occupation, sub_df["Salary"].mean()

start_time = time.time()

# Execute sequential computation
results = [compute_avg_salary_sequential(occupation) for occupation in occupations]
avg_salary = dict(results)

end_time = time.time()

# Print Execution Time
print(f"Sequential Execution Time: {end_time - start_time:.4f} seconds\n")


### PARALLEL CODE ######################################################################################################
# Initialize MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()   # Process ID
size = comm.Get_size()   # Total processes

# Start measuring time (only in root process)
if rank == 0:
    total_start_time = time.time()

# Root process reads the CSV and distributes data
df = None
occupations = None

if rank == 0:
    start_read_time_parallel = time.time()
    df = pd.read_csv("ph_occupation_dataset.csv")  # Load dataset
    end_read_time_parallel = time.time()
    print(f"CSV Read Time Parallel: {end_read_time_parallel - start_read_time_parallel:.4f} seconds")

    occupations = df["Occupation"].unique()

# Broadcast the full dataset and occupation list to all processes
df = comm.bcast(df, root=0)
occupations = comm.bcast(occupations, root=0)

# Distribute occupations among available processes
chunk_size = len(occupations) // size
start = rank * chunk_size
end = start + chunk_size if rank != size - 1 else len(occupations)
assigned_occupations = occupations[start:end]

# Function to compute average salary per occupation
def compute_avg_salary_parallel(occupation):
    sub_df = df[df["Occupation"] == occupation]
    record_count = len(sub_df)  # Count records
    avg_salary = sub_df["Salary"].mean()
    return occupation, (record_count, avg_salary)  # Return tuple (record count, avg salary)

# Each process computes salary for its assigned occupations
local_start_time = time.time()
local_results = {occupation: compute_avg_salary_parallel(occupation)[1] for occupation in assigned_occupations}
local_end_time = time.time()
local_processing_time = local_end_time - local_start_time

# Gather results at root process
all_results = comm.gather(local_results, root=0)

# Measure final time (only in root process)
if rank == 0:
    total_end_time = time.time()

    # Combine results from all processes
    final_salary_per_occupation = {}
    for result in all_results:
        if result:
            final_salary_per_occupation.update(result)

    # Display execution time
    print(f"MPI Parallel Execution Time: {total_end_time - total_start_time:.4f} seconds")

    # Display Speedup
    speedup = (end_time - start_time) / (total_end_time - total_start_time)
    print(f"\nSpeedup: {speedup:.4f}x")

    # Display Efficiency
    print(f"Efficiency: {(speedup / size) * 100:.2f}%")

    # Display computed Salary by occupation
    print("\nComputed Data per Occupation: ")
    print("{:<20}{:<15}{:<10}".format("Occupation", "Record Count", "Average Salary"))
    print("================================================")
    for occupation, (record_count, avg_salary) in final_salary_per_occupation.items():
        print(f"{occupation:<20}{record_count:<15}{avg_salary:<5.2f}")

# Print each process's local execution time
print(f"\nProcess {rank} Local Computation Time: {local_processing_time:.4f} seconds")

### VISUALIZATION ######################################################################################################
if rank == 0:
    # Convert results to a DataFrame for visualization
    result_df = pd.DataFrame(final_salary_per_occupation.items(), columns=["Occupation", "Data"])
    result_df[["Record Count", "Average Salary"]] = pd.DataFrame(result_df["Data"].tolist(), index=result_df.index)
    result_df.drop(columns=["Data"], inplace=True)  # Remove the old column

    # Sort by average salary for better visualization
    result_df = result_df.sort_values(by="Average Salary", ascending=False)

    # Set Seaborn theme
    sns.set_theme(style="whitegrid")

    # Create bar plot for average salaries per occupation
    plt.figure(figsize=(12, 6))
    sns.barplot(x="Average Salary", y="Occupation", data=result_df, hue="Occupation", dodge=False, palette="coolwarm", legend=False)
    plt.xlabel("Average Salary")
    plt.ylabel("Occupation")
    plt.title("Average Salary per Occupation")
    plt.show()

