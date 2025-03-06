#   PROBLEM 3: COUNT EMPLOYEES PER OCCUPATION IN EACH REGION

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

# Get Unique Region-Occupation pairs
unique_pairs = df.groupby(["Region", "Occupation"]).size().reset_index(name="Employee Count")

# Sequential execution time
start_time_sequential = time.time()

# Convert to dictionary: {(region, occupation): count}
sequential_results = {(row["Region"], row["Occupation"]): row["Employee Count"] for _, row in unique_pairs.iterrows()}

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
unique_pairs = None

if rank == 0:
    start_read_time_parallel = time.time()
    df = pd.read_csv("ph_occupation_dataset.csv")  # Load dataset
    end_read_time_parallel = time.time()
    print(f"CSV Read Time Parallel: {end_read_time_parallel - start_read_time_parallel:.4f} seconds")

    unique_pairs = df.groupby(["Region", "Occupation"]).size().reset_index(name="Employee Count")

# Broadcast the dataset to all processes
df = comm.bcast(df, root=0)
unique_pairs = comm.bcast(unique_pairs, root=0)

# Split the workload across processes
chunk_size = len(unique_pairs) // size
start = rank * chunk_size
end = start + chunk_size if rank != size - 1 else len(unique_pairs)
assigned_pairs = unique_pairs.iloc[start:end]

# Local computation per process
local_start_time = time.time()
local_results = {(row["Region"], row["Occupation"]): row["Employee Count"] for _, row in assigned_pairs.iterrows()}
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

    # Display computed counts
    print("\nEmployee Count per Occupation in Each Region:")
    print("{:<20}{:<20}{:<15}".format("Region", "Occupation", "Employee Count"))
    print("=" * 60)
    for (region, occupation), count in sorted(final_results.items()):
        print(f"{region:<20}{occupation:<20}{count:<15}")

# Print each process's local execution time
print(f"\nProcess {rank} Local Computation Time: {local_processing_time:.4f} seconds")


### VISUALIZATION ######################################################################################################
import re
if rank == 0:
    # Convert results to DataFrame for visualization
    result_df = pd.DataFrame(final_results.items(), columns=["Region_Occupation", "Employee Count"])
    result_df[["Region", "Occupation"]] = pd.DataFrame(result_df["Region_Occupation"].tolist(), index=result_df.index)
    result_df.drop(columns=["Region_Occupation"], inplace=True)
    result_df = result_df.sort_values(by="Employee Count", ascending=False)

    # Extract numeric part from Region for sorting
    def extract_region_number(region):
        match = re.search(r'\d+', region)  # Find numeric part
        return int(match.group()) if match else float('inf')  

    result_df["Region"] = result_df["Region"].astype(str)  # Ensure Region is string
    sorted_regions = sorted(result_df["Region"].unique(), key=extract_region_number)  # Sort numerically (ascending)

    # Ensure Occupation is sorted alphabetically
    sorted_occupations = sorted(result_df["Occupation"].unique())
    sns.set_theme(style="whitegrid")

    plt.figure(figsize=(16, 8)) 
    ax = sns.barplot(
        x="Employee Count", 
        y="Region",
        hue="Occupation", 
        data=result_df, 
        dodge=True, 
        palette="coolwarm", 
        order=sorted_regions,  # Ensure Regions are plotted in ascending order
        hue_order=sorted_occupations  # Ensure Occupations are sorted alphabetically
    )

    plt.xlabel("Employee Count", fontsize=14)
    plt.ylabel("Region", fontsize=14)  # Updated label
    plt.title("Number of Employees per Region in Each Occupation", fontsize=16)  # Updated title
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.legend(title="Occupation", bbox_to_anchor=(1.05, 1), loc="upper left")  # Legend updated
    plt.show()
