<?xml version="1.0" encoding="UTF-8"?>
<!-- 
    EAC-CPF to Apache Solr Input Document Format Transform
    Copyright 2013 eScholarship Research Centre, University of Melbourne
    
    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at
    
        http://www.apache.org/licenses/LICENSE-2.0
    
    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
-->
<xsl:stylesheet 
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
    xmlns:str="http://exslt.org/strings"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:mwg="http://www.metadataworkinggroup.com/schemas/collections/"
    version="1.0">

    <!-- <xsl:import href="../lib/common.xsl" /> -->

    <xsl:output method="text" indent="yes" encoding="UTF-8" omit-xml-declaration="yes" />
    <xsl:template match="/">
        <add>
            <doc>
                <field name="title"><xsl:value-of select="/rdf:RDF/rdf:Description/dc:title/rdf:Alt/rdf:li" /></field>
                <field name="description"><xsl:value-of select="/rdf:RDF/rdf:Description/dc:description/rdf:Alt/rdf:li" /></field>
                <field name="date_from"><xsl:value-of select="/rdf:RDF/rdf:Description/dc:date/rdf:Seq/rdf:li" /></field>
                <field name="collection_uri"><xsl:value-of select="/rdf:RDF/rdf:Description[2]/mwg:Collections/rdf:Bag/rdf:li/mwg:CollectionURI" /></field>
            </doc>
        </add>
    </xsl:template>
</xsl:stylesheet>