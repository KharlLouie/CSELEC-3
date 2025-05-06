#   PROBLEM 5: EMPLOYEE COUNT & AVERAGE SALARY PER OCCUPATION

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

# Sequential execution time
start_time_sequential = time.time()

# Compute employee count & average salary per occupation
sequential_results = df.groupby("Occupation")["Salary"].agg(["count", "mean"]).reset_index()
sequential_results.columns = ["Occupation", "Employee Count", "Average Salary"]
sequential_results = sequential_results.set_index("Occupation").to_dict("index")

end_time_sequential = time.time()
print(f"Sequential Execution Time: {end_time_sequential - start_time_sequential:.4f} seconds\n")


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

# Broadcast the dataset and occupations list
df = comm.bcast(df, root=0)
occupations = comm.bcast(occupations, root=0)

# Split workload across processes
chunk_size = len(occupations) // size
start = rank * chunk_size
end = start + chunk_size if rank != size - 1 else len(occupations)
assigned_occupations = occupations[start:end]

# Local computation per process
local_start_time = time.time()
local_results = {occupation: {
                    "Employee Count": df[df["Occupation"] == occupation].shape[0],
                    "Average Salary": df[df["Occupation"] == occupation]["Salary"].mean()
                }
                for occupation in assigned_occupations}
local_end_time = time.time()
local_processing_time = local_end_time - local_start_time

# Gather results at root process
all_results = comm.gather(local_results, root=0)

# Root process combines results
if rank == 0:
    total_end_time = time.time()

    final_results = {}
    for result in all_results:
        if result:
            final_results.update(result)

    # Display execution time
    print(f"MPI Parallel Execution Time: {total_end_time - total_start_time:.4f} seconds")

    # Compute speedup
    speedup = (end_time_sequential - start_time_sequential) / (total_end_time - total_start_time)
    print(f"\nSpeedup: {speedup:.4f}x")

    # Compute efficiency
    print(f"Efficiency: {(speedup / size) * 100:.2f}%")

    # Display sorted results
    print("\nEmployee Count & Average Salary per Occupation (Sorted): ")
    print("{:<30}{:<20}{:<20}".format("Occupation", "Employee Count", "Average Salary"))
    print("=" * 70)
    for occupation, data in sorted(final_results.items(), key=lambda x: x[0]):
        print(f"{occupation:<30}{data['Employee Count']:<20}{data['Average Salary']:<20.2f}")

# Print each process's local execution time
print(f"\nProcess {rank} Local Computation Time: {local_processing_time:.4f} seconds")


### VISUALIZATION ######################################################################################################
if rank == 0:
    # Convert results to DataFrame for visualization
    result_df = pd.DataFrame(final_results).T.reset_index().rename(columns={"index": "Occupation"})

    # Sort occupations alphabetically
    result_df = result_df.sort_values(by="Occupation")

    # Set Seaborn theme
    sns.set_theme(style="whitegrid")

    # Create bar plots for employee count & average salary per occupation
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Bar plot for employee count
    color1 = "orange"
    ax1.set_xlabel("Occupation")
    ax1.set_ylabel("Employee Count", color=color1)
    sns.barplot(x="Occupation", y="Employee Count", data=result_df, color=color1, ax=ax1)
    ax1.tick_params(axis="y", labelcolor=color1)
    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=90)

    # Create another y-axis for average salary
    ax2 = ax1.twinx()
    color2 = "blue"
    ax2.set_ylabel("Average Salary", color=color2)
    sns.lineplot(x="Occupation", y="Average Salary", data=result_df, color=color2, marker="o", ax=ax2)
    ax2.tick_params(axis="y", labelcolor=color2)

    # Add title and show the plot
    plt.title("Employee Count & Average Salary per Occupation")
    plt.show()
