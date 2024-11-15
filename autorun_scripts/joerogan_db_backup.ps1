# Define the source file path
$sourceFile = "C:\Users\Administrator\Desktop\joerogan.db"

# Define the destination folder path
$destinationFolder = "C:\Users\Administrator\Desktop\previous_dbs"

# Get the current date in Year_Month_Day format
$date = Get-Date -Format "yyyy_MM_dd"

# Set the base destination file name with date
$baseDestinationFile = "$destinationFolder\joerogan_$date.db"
$destinationFile = $baseDestinationFile

# Initialize a counter for duplicate file names
$counter = 1

# Check if a file with the same name already exists, and if so, find a unique name
while (Test-Path -Path $destinationFile) {
    # Append a counter to the file name if a file with the same name already exists
    $destinationFile = "$destinationFolder\joerogan_$date ($counter).db"
    $counter++
}

# Check if the destination folder exists, create it if not
if (!(Test-Path -Path $destinationFolder)) {
    New-Item -ItemType Directory -Path $destinationFolder
}

# Move and rename the file
Copy-Item -Path $sourceFile -Destination $destinationFile
