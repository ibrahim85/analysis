# practiceanatomy.com

The data set is based on the online system
[practiceanatomy.com](https://practiceanatomy.com). The system is
available in Czech and English, most users are from Czech
Republic ({cz_percentage} %) and Slovakia ({sk_percentage} %). The system uses
adaptive algorithms for choosing questions, these algorithms are described in
detail in [[1](#references)] and [[2](#references)].

This data set is static and captures users' interactions from
{collection_start} to {collection_end}. The application provides both free and
premium content, but interactions with the premium content are excluded from
the data set.

The basic statistics of the data set are as follows:

  - {total_learners:,} learners;
  - {total_items:,} anatomical items
  - {total_answers:,} answers

## Description

The dataset contains [1 CSV file](answers.csv) (commas are used as delimiter)
containing answers of users practicing location of anatomical structures. The
whole data set with this readme file can be [downloaded as
ZIP archive](http://data.practiceanatomy.com/public-data.zip).

### Answers

|        Column       | Description                                                                                              |
|:-------------------:|----------------------------------------------------------------------------------------------------------|
|          id         | answer identifier                                                                                        |
|         user        | user's identifier                                                                                        |
|     item_asked      | identifier of the asked term                                                                             |
|     term_name_asked | name of the asked term                                                                                   |
|   item_answered     | identifier of the answered term, empty if the user answered "I don't know"                               |
|  term_name_answered | name of the answered term                                                                                |
|      context_name   | name of the image (context)                                                                              |
|        type         | type of the answer: (t2d) find the given term on the image; (d2t) pick the name for the highlighted term |
|        options      | number of options (the asked term included)                                                              |
|          time       | datetime when the answer was inserted to the system                                                      |
|     response_time   | how much time the answer took (measured in milliseconds)                                                 |
|      ip_country     | country retrieved from the user’s IP address                                                             |
|        ip_id        | meaningless identifier of the user’s IP address                                                          |
|      lang           | language of the terminology (cs: Czech only, la (cs): Latin with some Czech, en: English only, la (en): Latin with some English |
|   locations_asked   | location of the asked term on the human body (JSON)                                                      |
|    systems_asked    | organ systems of the asked term (JSON)                                                                   |
|  locations_answered | locations of the answered term on the human body (JSON)                                                  |
|   systems_answered  | organ systems of the answered term (JSON)                                                                |
|  practice_filter    | filter used by the user to practice (JSON)                                                               |



## Ethical and privacy considerations:

The used educational system is an open online system which
can be used by anybody and details about individual users are not available.
Users are identified only by their anonymous ID. Users can log into the system
using their Google or Facebook accounts; but this login is used only for
identifying the user within the system, it is not included in the data set.
Unlogged users are tracked using web browser cookies. The system also logs IP
address from which users access the system, the IP address is included in the
data set in anonymized form. We separately encode the country of origin, which
can be useful for analysis and its inclusion is not a privacy concern. The rest
of the IP address is replaced by meaningless identifier to preserve privacy.

## Terms of Use

The data set is available at [data.practiceanatomy.com](http://data.practiceanatomy.com).

### License

This data set is made available under Open Database License whose full text can
be found at http://opendatacommons.org/licenses/odbl/. Any rights in individual
contents of the database are licensed under the Database Contents License whose
text can be found http://opendatacommons.org/licenses/dbcl/

## References

 - **[1]** Papoušek, J., Pelánek, R. & Stanislav, V. [Adaptive Practice of Facts in Domains with Varied Prior Knowledge](http://www.fi.muni.cz/~xpelanek/publications/EDM14-adaptive-facts.pdf). In Educational Data Mining, 2014.
 - **[2]** Papoušek, J., & Pelánek, R. [Impact of adaptive educational system behaviour on student motivation](http://www.fi.muni.cz/~xpelanek/publications/aied15.pdf). In Artificial Intelligence in Education, 2015.
