#   PROBLEM 4: AVERAGE SALARY & STANDARD DEVIATION PER REGION

from mpi4py import MPI
import pandas as pd
import time
import matplotlib.pyplot as plt
import seaborn as sns
import re

### SEQUENTIAL CODE ####################################################################################################
# Read CSV file
start_read_time_sequential = time.time()
df = pd.read_csv("ph_occupation_dataset.csv")
end_read_time_sequential = time.time()
print(f"CSV Read Time Sequential: {end_read_time_sequential - start_read_time_sequential:.4f} seconds")

# Sequential execution time
start_time_sequential = time.time()

# Compute average salary & standard deviation per region
sequential_results = df.groupby("Region")["Salary"].agg(["mean", "std"]).reset_index()
sequential_results.columns = ["Region", "Average Salary", "Salary Std Dev"]
sequential_results = sequential_results.set_index("Region").to_dict("index")

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
regions = None

if rank == 0:
    start_read_time_parallel = time.time()
    df = pd.read_csv("ph_occupation_dataset.csv")  # Load dataset
    end_read_time_parallel = time.time()
    print(f"CSV Read Time Parallel: {end_read_time_parallel - start_read_time_parallel:.4f} seconds")

    regions = df["Region"].unique()

# Broadcast the dataset and regions list
df = comm.bcast(df, root=0)
regions = comm.bcast(regions, root=0)

# Split workload across processes
chunk_size = len(regions) // size
start = rank * chunk_size
end = start + chunk_size if rank != size - 1 else len(regions)
assigned_regions = regions[start:end]

# Local computation per process
local_start_time = time.time()
local_results = {region: {
                    "Average Salary": df[df["Region"] == region]["Salary"].mean(),
                    "Salary Std Dev": df[df["Region"] == region]["Salary"].std()
                }
                for region in assigned_regions}
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
    def natural_sort_key(region):
        numbers = re.findall(r'\d+', region)  # Extract numbers from region
        return (int(numbers[0]) if numbers else float('inf'), region)  # Sort numerically if possible

    print("\nAverage Salary & Standard Deviation per Region (Sorted): ")
    print("{:<20}{:<20}{:<20}".format("Region", "Average Salary", "Salary Std Dev"))
    print("=" * 60)
    for region, data in sorted(final_results.items(), key=lambda x: natural_sort_key(x[0])):
        print(f"{region:<20}{data['Average Salary']:<20.2f}{data['Salary Std Dev']:<20.2f}")

# Print each process's local execution time
print(f"\nProcess {rank} Local Computation Time: {local_processing_time:.4f} seconds")


### VISUALIZATION ######################################################################################################
if rank == 0:
    # Convert results to DataFrame for visualization
    result_df = pd.DataFrame(final_results).T.reset_index().rename(columns={"index": "Region"})

    # Sort regions naturally
    result_df = result_df.sort_values(by="Region", key=lambda x: x.map(natural_sort_key))

    # Set Seaborn theme
    sns.set_theme(style="whitegrid")

    # Create bar plot for average salary & standard deviation per region
    plt.figure(figsize=(12, 6))
    sns.barplot(x="Average Salary", y="Region", data=result_df, color="blue", label="Average Salary")
    sns.barplot(x="Salary Std Dev", y="Region", data=result_df, color="orange", label="Salary Std Dev")

    # Add labels and title
    plt.xlabel("Salary")
    plt.ylabel("Region")
    plt.title("Average Salary & Standard Deviation per Region")
    plt.legend()
    plt.show()
