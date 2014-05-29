# USPTO patent tools

> Tools for parsing and extracting information from USPTO patents


## Motivation

In 2012, I published a paper on the impact of misspellings in patents. Here is
the abstract:

> The search in patent databases is a risky business compared to the search in
> other domains. A single document that is relevant but overlooked during a
> patent search can turn into an expensive proposition. While recent research
> engages in specialized mod- els and algorithms to improve the effectiveness
> of patent retrieval, we bring another aspect into focus: the detection and
> exploitation of patent inconsistencies. In particular, we analyze spelling
> errors in the assignee field of patents granted by the United States Patent &
> Trademark Office. We introduce technology in order to improve retrieval
> effectiveness despite the presence of typographical ambiguities. In this
> regard, we (1) quantify spelling errors in terms of edit distance and
> phonological dissimilarity and (2) render error detection as a learning
> problem that combines word dissimilarities with patent meta-features. For the
> task of finding all patents of a company, our approach improves recall from
> 96.7% (when using a state-of-the-art patent search engine) to 99.5%, while
> precision is compromised by only 3.7%.

You can read the full paper [here][eacl12].

Processing the XML patent data set wasn't straightforward, because some
files were corrupt, and the SGML changed from year to year. Please find in this
repository some parsers written in Python. Beware, that I just duplicated the
code for different years or use-cases.

Refer to the usage information via ``--help''.


# Authors

**Dennis Hoppe**

+ [github/hopped](https://github.com/hopped)


## License
Copyright 2014 Dennis Hoppe.

[MIT License](LICENSE).




[eacl12]: https://github.com/hopped/publications/blob/master/papers/hoppe-2012a.pdf
