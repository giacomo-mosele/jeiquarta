def da_mettere(line):
    if "WARNING" not in line:
        return False
    
    if "Incrementato di 0 punti" in line:
        return False
    
    if "This is a development server" in line:
        return False
    
    return True

file_read = open("log.log", "r")

#lines = file_read.read().split("\n")
warnings = [f"{line[:19]} - {line[36:]}" for line in file_read if da_mettere(line)]

file_read.close()


file_write = open("sorted_log.txt", "w", encoding="utf-8")

file_write.write("\n".join(warnings))

file_write.close()