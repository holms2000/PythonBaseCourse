def insert_digit():
    num_list = input().split()
    n,d = [int(num_list[i]) for i in range(len(num_list))]
    string = input()
    insert_digit = False
    string_out=""
    for i in range(0,n):
        if int(string[i]) >= d:
            string_out+=string[i]
        else:
            string_out+=str(d)
            for j in range(i,n):
                string_out+=string[j]
            insert_digit = True
            break
    if insert_digit == False:
        string_out+=str(d)
    return string_out

t = int(input())
for _ in range(t):
    print(insert_digit())