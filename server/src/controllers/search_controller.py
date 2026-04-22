import logging
from fastapi import HTTPException
from src.configs.db_config import search_db
import json
from src.utility.reform_queries import reformulate_query

index_option = {
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "max_ngram_diff": 20,
    "analysis": {
      "char_filter": {
        "remove_dots": {
          "type": "pattern_replace",
          "pattern": "\\.",
          "replacement": ""
        },
        "remove_spaces": {
            "type": "pattern_replace",
            "pattern": "\\s+",
            "replacement": ""
        }   ,
      },
      "normalizer": {
        "lowercase_normalizer": {
          "type": "custom",
          "filter": ["lowercase", "asciifolding"]
        }
      },
      "tokenizer": {
        "ngram_tokenizer": {
          "type": "ngram",
          "min_gram": 3,
          "max_gram": 20,
          "token_chars": ["letter"]
        }
      },
      "analyzer": {
        "name_analyzer": {
          "type": "custom",
          "tokenizer": "keyword",
          "char_filter": ["remove_dots","remove_spaces"],
          "filter": ["lowercase", "asciifolding"]
        },
        "ngram_analyzer": {
          "type": "custom",
          "tokenizer": "ngram_tokenizer",
          "char_filter": ["remove_dots"],
          "filter": ["lowercase", "asciifolding"]
        },
        "standard_lower": {
          "type": "custom",
          "tokenizer": "standard",
          "char_filter": ["remove_dots"],
          "filter": ["lowercase", "asciifolding"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "id": { "type": "integer" },

      "title": {
        "type": "text",
        "analyzer": "standard_lower",
        "fields": {
          "ngram": {
            "type": "text",
            "analyzer": "ngram_analyzer"
          }
        }
      },

      "description": {
        "type": "text",
        "analyzer": "standard_lower"
      },

      "publisher": {
        "type": "keyword",
        "normalizer": "lowercase_normalizer",
        "fields":{
            "text":{
                "type": "text",
                "analyzer": "standard_lower"
            },
            "concat": {
                "type": "text",
                "analyzer": "name_analyzer"
            },
            "ngram":{
                "type": "text",
                "analyzer": "ngram_analyzer"
            }
        }
        },

      "publication_year": { "type": "integer" },

      "edition": { "type": "keyword" },

      "language": {
        "type": "keyword",
        "normalizer": "lowercase_normalizer"
      },

      "authors": {
        "type": "text",
        "analyzer": "standard_lower",
        "fields": {
          "ngram": {
            "type": "text",
            "analyzer": "ngram_analyzer"
          },
          "keyword": {
            "type": "keyword",
            "normalizer": "lowercase_normalizer"
          },
          "concat": {
            "type": "text",
            "analyzer": "name_analyzer"
          }
        }
      },

      "categories": {
        "type": "keyword",
        "normalizer": "lowercase_normalizer",
        "fields": {
          "text": { "type": "text", "analyzer": "standard_lower" },
        }
      },

      "tags": {
        "type": "text",
        "analyzer": "standard_lower",
        "fields": {
          "keyword": { "type": "keyword" },
        }
      },

      "pages": { "type": "integer" },

      "isbn": { "type": "keyword" }
    }
  }
}

class SearchController:

    def __init__(self):
        self.index_name = "books"

    async def init_index(self):
        """Check if the index exists, and create it if it doesn't"""
        exists = await search_db.client.indices.exists(index=self.index_name)
        if not exists:
            logging.info(f"Creating index '{self.index_name}'")
            await search_db.create_index(
                index=self.index_name,
                settings=index_option
            )
        else:
            logging.info(f"Index '{self.index_name}' already exists")

    async def index_book(self, book: dict):
        """Index a single book document in Elasticsearch"""
        response = await search_db.index(
            index=self.index_name,
            id=book["id"],
            document=book
        )
        if response.get("result") not in ["created", "updated"]:
            raise HTTPException(status_code=500, detail="Failed to index book")
        return response

    async def index_books_bulk(self, documents: list):
        """Index multiple book documents in Elasticsearch"""
        if len(documents) == 0:
            raise HTTPException(status_code=400, detail="No documents to index")
        
        response = await search_db.index_bulk(
            index=self.index_name,
            documents=documents
        )

        return {"success_count": len(response["items"]), "error_count": response["errors"]}
    
    async def auto_complete(self, query: str, filters: dict = None):

        filter_clauses = []

        if filters:
            if filters.get("publisher"):
                filter_clauses.append({
                    "term": {
                        "publisher": filters["publisher"].lower()
                    }
                })

            if filters.get("category"):
                filter_clauses.append({
                    "term": {
                        "categories": filters["category"].lower()
                    }
                })

            if filters.get("tag"):
                filter_clauses.append({
                    "term": {
                        "tags.keyword": filters["tag"].lower()
                    }
                })

            if filters.get("language"):
                filter_clauses.append({
                    "term": {
                        "language.keyword": filters["language"].lower()
                    }
                })

            if filters.get("year_gte") or filters.get("year_lte"):
                range_query = {}
                if filters.get("year_gte"):
                    range_query["gte"] = filters["year_gte"]
                if filters.get("year_lte"):
                    range_query["lte"] = filters["year_lte"]

                filter_clauses.append({
                    "range": {
                        "publication_year": range_query
                    }
                })

            if filters.get("author"):
                filter_clauses.append({
                       "term":{
                            "authors.keyword": filters["author"].lower()
                       }
                    
                })

        search_query = {
            "bool": {
                "should": [

                {
                    "multi_match": {
                    "query": query,
                    "type": "cross_fields",
                    "fields": [
                        "title^5",
                        "authors^4",
                        "tags^3",
                        "publisher.text^3",
                        "categories.text^2"
                    ]
                    }
                },

                {
                    "match": {
                    "publisher.concat": {
                        "query": query,
                        "boost": 5
                    }
                    }
                },

                {
                    "match": {
                    "authors.concat": {
                        "query": query,
                        "boost": 6
                    }
                    }
                },

                {
                    "multi_match": {
                    "query": query,
                    "fields": [
                        "authors.ngram^3",
                        "title.ngram^2"
                    ]
                    }
                }

                ],
                "minimum_should_match": 1,
                "filter": filter_clauses
            }
            }
        print(filter_clauses)
        response = await search_db.search(
            index=self.index_name,
            query=search_query
        )

        if(response.get("hits") is None):
            raise HTTPException(status_code=500, detail="Search query failed")
        

        return response["hits"]["hits"]
    
    async def search(self, query: str, filters: dict = None):
        filter_clauses = []

        if filters:
            if filters.get("publisher"):
                filter_clauses.append({
                    "term": {
                        "publisher": filters["publisher"].lower()
                    }
                })

            if filters.get("category"):
                filter_clauses.append({
                    "term": {
                        "categories": filters["category"].lower()
                    }
                })

            if filters.get("tag"):
                filter_clauses.append({
                    "term": {
                        "tags.keyword": filters["tag"].lower()
                    }
                })

            if filters.get("language"):
                filter_clauses.append({
                    "term": {
                        "language.keyword": filters["language"].lower()
                    }
                })

            if filters.get("year_gte") or filters.get("year_lte"):
                range_query = {}
                if filters.get("year_gte"):
                    range_query["gte"] = filters["year_gte"]
                if filters.get("year_lte"):
                    range_query["lte"] = filters["year_lte"]

                filter_clauses.append({
                    "range": {
                        "publication_year": range_query
                    }
                })

            if filters.get("author"):
                filter_clauses.append({
                       "term":{
                            "authors.keyword": filters["author"].lower()
                       }
                    
                })


            [keyword_query, cleaned_query] = reformulate_query(query)

            print("Keyword Query:", keyword_query)
            # print("Variants:", variants)
            print("Cleaned Query:", cleaned_query)

            search_query = {
                "bool": {
                    "should": [],
                    "filter": filter_clauses
                }
            }

            # ---- 1. MAIN QUERY (TOPIC DOMINANT) ----
            if cleaned_query:
                search_query["bool"]["should"].append({
                    "multi_match": {
                        "query": cleaned_query,
                        "type": "cross_fields",
                        "fields": [
                            "title^6",
                            "tags^5",
                            "categories.text^6",
                            "publisher.text^2"
                        ],
                        "boost": 4
                    }
                })

                search_query["bool"]["should"].append({
                    "multi_match": {
                        "query": cleaned_query,
                        "type": "best_fields",
                        "fields": [
                            "title^5",
                            "tags^3",
                            "categories.text^4",
                            "authors^1"
                        ],
                        "fuzziness": "AUTO",
                        "boost": 3.5
                    }
                })

            # ---- 2. KEYWORD SIGNALS (CONTROLLED) ----
            for key, values in keyword_query.items():
                if not values:
                    continue

                unique_values = set(values)

                for value in unique_values:

                    if key == "author":
                        search_query["bool"]["should"].append({
                            "multi_match": {
                                "query": value,
                                "fields": [
                                    "authors^2",
                                    "authors.ngram"
                                ],
                                "boost": 1
                            }
                        })

                    elif key == "publisher":
                        search_query["bool"]["should"].append({
                            "multi_match": {
                                "query": value,
                                "fields": [
                                    "publisher.concat^3",
                                    "publisher.text^2",
                                    "publisher.ngram"
                                ],
                                "boost": 1
                            }
                        })

                    elif key == "category":
                        search_query["bool"]["should"].append({
                            "multi_match": {
                                "query": value,
                                "fields": [
                                    "categories.text^5"
                                ],
                                "boost": 2.5
                            }
                        })

                    elif key == "tag":
                        search_query["bool"]["should"].append({
                            "match": {
                                "tags": {
                                    "query": value,
                                    "boost": 2.5
                                }
                            }
                        })

                    elif key == "edition":
                        search_query["bool"]["should"].append({
                            "term": {
                                "edition": {
                                    "value": value,
                                    "boost": 2
                                }
                            }
                        })

            # ---- 3. ISBN EXACT MATCH ----
            search_query["bool"]["should"].append({
                "term": {
                    "isbn.keyword": {
                        "value": query,
                        "boost": 15
                    }
                }
            })

            # ---- 4. CLEAN PHRASE BOOST ----
            if cleaned_query:
                search_query["bool"]["should"].append({
                    "match_phrase": {
                        "title": {
                            "query": cleaned_query,
                            "boost": 3
                        }
                    }
                })

            # ---- 5. WEAK FALLBACK ----
            if cleaned_query:
                search_query["bool"]["should"].append({
                    "match": {
                        "description": {
                            "query": cleaned_query,
                            "boost": 1.2
                        }
                    }
                })

            # ---- 6. CONTROL SHOULD ----
            search_query["bool"]["minimum_should_match"] = 1

            response = await search_db.search(
            index=self.index_name,
            query=search_query
        )
        print (json.dumps(search_query, indent=2))
        # print(response)
        return response["hits"]["hits"]


search_controller = SearchController()