import os

print("Choose an option:")
print("1. gesture controller for runing games (temple run)")
print("2. gesture controller for racing games (hill climb)")
print("3. voice controller for runing games(temple run)")
print("4. voice controller for racing games(hill climber)")

choice = input("Enter 1 , 2 or 3: ")

if choice == "1":
    os.system("python GG_1.py")  # replace 'file1.py' with your first file name
elif choice == "2":
    os.system("python GG_2.py")  # replace 'file2.py' with your second file name
elif choice =="3":
    os.system("python VV_1.py")
elif choice =="4":
    os.system("python VV_2.py")
else:
    print("Invalid choice!")
