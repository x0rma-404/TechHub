a=input('Ip:')
a=a+'.'
l=['']
k=0
for i in a:
    if i=='.':
        l+=[k]
        k=0
    else:
        k=k*10+int(i)
e=int(input('Number:'))
Submit_mask='255.'*(e//8)+str(2**8-1-(2**(8-e%8)-1))+'.0'*(4-e//8-1)
print('Submit_mask:'+Submit_mask)
Host_bitlerinin_sayi=32-e
Hostlarin_maxi=(2**Host_bitlerinin_sayi)-2
print('Host_bitlerinin_sayi:',Host_bitlerinin_sayi,'Hostlarin_maxi:',Hostlarin_maxi)
x=255-(2**8-1-(2**(8-e%8)-1))
nw_count=e//8
nw_part=''
i=x
k=0
while l[nw_count+1]>i:
    k+=(x+1)
    i+=(x+1)
for j in range(1,nw_count+1):
    nw_part+=str(l[j])+'.'
Network=nw_part+str(k)+'.0'*(4-e//8-1)
print('Network:',Network)
Broadcast=nw_part+str(i)+'.255'*(4-e//8-1)
print('Broadcast:'+Broadcast)
l_n=len(Network)
l_b=len(Broadcast)
ilk=Network[0:l_n-1]
ilk+=str(int(Network[l_n-1])+1)
print('Ilk:'+ilk)
son=Broadcast[0:l_b-1]
son+=str(int(Broadcast[l_b-1])-1)
print('Son:'+son)