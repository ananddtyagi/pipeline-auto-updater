import React, { useRef } from 'react';
import Papa from 'papaparse';

const FileUpload = ({ onDataLoaded }) => {
  const fileInputRef = useRef(null);

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    
    if (!file) return;
    
    if (file.type !== 'text/csv') {
      alert('Please upload a CSV file');
      return;
    }

    Papa.parse(file, {
      header: true,
      complete: (results) => {
        const { data, meta } = results;
        
        if (!meta.fields.includes('Input') || !meta.fields.includes('Expected Output')) {
          alert('CSV file must contain "Input" and "Expected Output" columns');
          return;
        }

        const formattedData = data.map((row, index) => ({
          id: index,
          input: row.Input,
          expectedOutput: row['Expected Output'],
          botOutput: '',
          notes: '',
          betterAnswer: ''
        }));

        onDataLoaded(formattedData);
      },
      error: (error) => {
        alert(`Error parsing CSV file: ${error.message}`);
      }
    });
  };

  return (
    <div className="m-5 p-5 border-2 border-dashed border-gray-300 rounded-lg text-center">
      <input
        type="file"
        ref={fileInputRef}
        accept=".csv"
        onChange={handleFileUpload}
        className="p-2 text-gray-700 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
      />
    </div>
  );
};

export default FileUpload;