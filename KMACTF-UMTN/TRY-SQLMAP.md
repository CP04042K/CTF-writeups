Challenge: http://try-sqlmap.ctf.actvn.edu.vn/

![image](https://user-images.githubusercontent.com/35491855/154800109-eeb85e75-0387-4288-b1a1-ae2d7c4d058a.png)


As the title of the challenge, it tells us to try `SQL Map`, but in this case this powerful tool is not gonna help us get the flag, but it gave us a hint. 

![image](https://user-images.githubusercontent.com/35491855/154800002-0e97d92c-a1dd-4f22-b57d-4cd5e115c2b8.png)

This website can be exploited with `Error Based SQLi`, using some functions like `extractvalue` and `updatexml`. If you add extra character such as a single quote to the parameter, you will get the error, that mean the server respond the error message whenever there is an error. 

![image](https://user-images.githubusercontent.com/35491855/154800167-04ea9950-7006-4da8-837d-d338acb8a30a.png)

Easy peasy lemon squeezy, let's give it a try, by using the the `extractvalue` function i can get the database name

![image](https://user-images.githubusercontent.com/35491855/154800214-24d964a9-c7b2-4c07-8590-fa30ceadfdc7.png)

Now let's move on, get the table name and then the column. 

![image](https://user-images.githubusercontent.com/35491855/154800263-2bf1e1a2-84bc-4d82-aee8-82d1127638a6.png)

Wait, it show us the index page's content, something is not right here, we should have got the table by now. Well, After numerous attempts, i finally found out that the input length is limited to 100 characters and by reading the hint, i can guess that the output length is also limited to 32 characters

![image](https://user-images.githubusercontent.com/35491855/154800416-1645ab03-535e-4789-ac0a-a01d546a31f0.png)

Good, now we have to find a way to reduce the length of the query and as the length of flag table name is longer that 32 characters, we will have to use `mid` function to bypass the output check. This is my query:

`http://try-sqlmap.ctf.actvn.edu.vn/?order=extractvalue(0,concat(0,(SELECT+mid(table_name,1,31)+FROM+information_schema.tables+limit+1)))`

![image](https://user-images.githubusercontent.com/35491855/154800852-16a65504-d608-4e0f-9763-32be0763c9ab.png)

As you can see, we have successfully extracted the first 32 characters of the table name, as we increase the index we'll be able to know the whole string. I used `limit 1` as the table name record is coincidentally the first record in `information_schema.tables`. Keep increasing the index value of the `mid` function, we get the whole name: `flahga123456789xxsxx012xxxxxxxxx34567xx1`

Using the same technique, we also get the column name as it's also the first record in `information_schema.columns`, query: 
`http://try-sqlmap.ctf.actvn.edu.vn/?order=extractvalue(0,concat(0,(SELECT+mid(column_name,1,31)+FROM+information_schema.columns+limit+1)))`

![image](https://user-images.githubusercontent.com/35491855/154801196-b86e8848-a097-40aa-aa01-f43360cbf19e.png)

Finally, extract the flag:

![image](https://user-images.githubusercontent.com/35491855/154801232-491692ec-733a-40d8-a11d-df7995bc3d60.png)

`http://try-sqlmap.ctf.actvn.edu.vn/?order=extractvalue(0,concat(0,(SELECT+mid(flag,1,31)+FROM+flahga123456789xxsxx012xxxxxxxxx34567xx1)))`

final flag: `KMACTF{X_Ooooooooooooorder_By_Nooooooooooooooooooone_SQLMaaaaaaaaaaaaaaaap?!!!!!!!!!!!!}`

