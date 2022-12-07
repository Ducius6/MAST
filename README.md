<h1>MAST Instructions</h1>

Code has two main classes one is MASTBuilder. In constructor it receives logic statement 
as String. Text is logic statement where AND is represented by *, OR is represented by +.
Each script program is encapsulated in {} braces. Script program contains some global_state key, 
some comparison operator and some value to compare with global_state.

Example of input text for MASTBuilder: <br/>
```python
text = "{time_in_millis < 450} + {time_in_millis < 560} * ({current_block == 256} + {time_in_millis >= 4})"
```



Main method of MASTBuilder is create_mast_object which returns hash of root node of MAST and
evidence list which is list of all leaf nodes in MAST. With each evidence you are able to traverse to root
of MAST and verify its belonging to the tree.

```python
mast_builder = MASTBuilder(text)
root_hash, evidence_list = mast_builder.create_mast_object()
```    

Other main class in the project is MASTVerification. In constructor it receives root hash, global state and evidence list
needed for executing script. Main method of the class is verify_mast which evaluates each script
sent in evidence list. After that by traversing the tree upwards it checks for each node
if it has correct hashes. Also if the node in the tree has AND operator it requires both
children nodes to be sent directly or by traversing from another leaf node to it.
Method verfy_mast returns True if each of the conditions fulfilled, if some condition is not then method raises Exception.

Example of creating MASTVerification and verifying tree:
```python
mast_verificator = MASTVerification(root_hash, global_state, [evidence_list[0]])
mast_verificator.verify_mast()
```   
 