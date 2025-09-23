# Kyle Versluis, 08/30/2025, Assignment 1
# Title: Simple String Searching
# Purpose: Simple string searching and analysis

# Sample excerpt given from the Hacker Manifesto
excerpt = """Another one got caught today, it's all over the papers. \
Teenager Arrested in Computer Crime Scandal, Hacker Arrested after Bank \
Tampering. Damn kids. They're all alike."""

# convert to lower case
excerpt = excerpt.lower()
# print start of output
print("\n*****START*****")
#display excerpt in lower case
print("\nLower case format:")
print(excerpt)
# counts the number of characters in the string
char_count = len(excerpt)
#display character count
print(f"\nFound...{char_count} characters.\n_____")
# split the string into words and count them
words = excerpt.split()
word_count = len(words)
#sort words in alphabetical order
word_sort = sorted(words)
#display sorted word list and count
print("\nSorted word list:")
print(word_sort)
print(f"\nFound...{word_count} words.\n_____")
# searches for specific words and counts occurrences
search_list = ["scandal", "arrested", "er", "good", "tomorrow"]
search_list_results = {}
for word in search_list:
    search_list_results[word] = excerpt.count(word)
# display word search results and count
print(f"\nWord search results:")
for word, count in search_list_results.items():
    print(f"{word}: {count}")
# print end of output
print("\n*****DONE*****\n")
