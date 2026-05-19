import os
old_face = ['01','02','03','04','05','06','07','08','09','10','11','12','13']
old_suit = ['h','c','d','s']
new_face = ['Ace', 'Two','Three','Four','Five','Six','Seven','Eight','Nine','Ten','Jack','Queen','King']
new_suit = ['_of_Hearts','_of_Clubs','_of_Diamonds','_of_Spades']
for i in range(len(old_face)):
  for j in range(len(old_suit)):
        os.rename(old_face[i] + old_suit[j] + '.gif', new_face[i] + new_suit[j] + '.gif' )
