import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { DocumentArrowUpIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';

function App() {
  const [files, setFiles] = useState({
    pdf: null,
    excel: null
  });
  
  const [pages, setPages] = useState({
    income: [],
    balance: [],
    cashFlow: []
  });
  
  const [loading, setLoading] = useState(false);

  // PDF File Upload
  const { getRootProps: getPdfRootProps, getInputProps: getPdfInputProps, isDragActive: isPdfDragActive } = useDropzone({
    accept: {
      'application/pdf': ['.pdf']
    },
    maxFiles: 1,
    onDrop: (acceptedFiles) => {
      setFiles(prev => ({
        ...prev,
        pdf: acceptedFiles[0]
      }));
    }
  });

  // Excel File Upload
  const { getRootProps: getExcelRootProps, getInputProps: getExcelInputProps, isDragActive: isExcelDragActive } = useDropzone({
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls']
    },
    maxFiles: 1,
    onDrop: (acceptedFiles) => {
      setFiles(prev => ({
        ...prev,
        excel: acceptedFiles[0]
      }));
    }
  });

  const handlePageChange = (statement, index, value) => {
    setPages(prev => ({
      ...prev,
      [statement]: prev[statement].map((page, i) => i === index ? value : page)
    }));
  };

  const addPage = (statement) => {
    setPages(prev => ({
      ...prev,
      [statement]: [...prev[statement], '']
    }));
  };

  const removePage = (statement, index) => {
    setPages(prev => ({
      ...prev,
      [statement]: prev[statement].filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!files.pdf || !files.excel) {
      alert('Please upload both PDF and Excel files');
      return;
    }

    if (!pages.income.length || !pages.balance.length || !pages.cashFlow.length) {
      alert('Please add at least one page number for each statement');
      return;
    }

    const integerPages = {
      income: pages.income.map(page => parseInt(page, 10)),
      balance: pages.balance.map(page => parseInt(page, 10)),
      cashFlow: pages.cashFlow.map(page => parseInt(page, 10))
    };

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('pdf_file', files.pdf);
      formData.append('excel_file', files.excel);
      formData.append('pages', JSON.stringify(integerPages));

      // Replace with your actual backend URL
      const response = await fetch('http://localhost:5000/process', {
        method: 'POST',
        body: formData
      });
      console.log(response)

      if (!response.ok) {
        throw new Error('Server responded with an error');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'processed_financial_statements.xlsx';
      link.click();
      
      alert('Files processed successfully!');
    } catch (error) {
      console.error('Error processing files:', error);
      alert('An error occurred while processing the files');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900">
            Financial Statement Extractor
          </h1>
          <p className="mt-2 text-gray-600">
            Upload your files and specify page numbers to process financial statements
          </p>
        </div>

        <div className="bg-white shadow rounded-lg p-6 space-y-6">
          {/* File Upload Section */}
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            {/* PDF Upload */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">PDF File</h3>
              <div
                {...getPdfRootProps()}
                className={clsx(
                  "border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors",
                  isPdfDragActive ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400"
                )}
              >
                <input {...getPdfInputProps()} />
                <DocumentArrowUpIcon className="mx-auto h-8 w-8 text-gray-400" />
                {files.pdf ? (
                  <p className="mt-2 text-sm text-gray-900">{files.pdf.name}</p>
                ) : (
                  <p className="mt-2 text-sm text-gray-500">
                    Drop PDF file here
                  </p>
                )}
              </div>
            </div>

            {/* Excel Upload */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">Excel File</h3>
              <div
                {...getExcelRootProps()}
                className={clsx(
                  "border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors",
                  isExcelDragActive ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400"
                )}
              >
                <input {...getExcelInputProps()} />
                <DocumentArrowUpIcon className="mx-auto h-8 w-8 text-gray-400" />
                {files.excel ? (
                  <p className="mt-2 text-sm text-gray-900">{files.excel.name}</p>
                ) : (
                  <p className="mt-2 text-sm text-gray-500">
                    Drop Excel file here
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Page Numbers Section */}
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-900">Statement Pages</h3>
            
            {/* Income Statement Pages */}
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <label className="block text-sm font-medium text-gray-700">
                  Income Statement Pages
                </label>
                <button
                  type="button"
                  onClick={() => addPage('income')}
                  className="text-sm text-blue-600 hover:text-blue-500"
                >
                  + Add Page
                </button>
              </div>
              {pages.income.map((page, index) => (
                <div key={index} className="flex gap-2">
                  <input
                    type="number"
                    value={page}
                    onChange={(e) => handlePageChange('income', index, e.target.value)}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    placeholder="Page number"
                  />
                  <button
                    type="button"
                    onClick={() => removePage('income', index)}
                    className="text-red-600 hover:text-red-500"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>

            {/* Balance Sheet Pages */}
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <label className="block text-sm font-medium text-gray-700">
                  Balance Sheet Pages
                </label>
                <button
                  type="button"
                  onClick={() => addPage('balance')}
                  className="text-sm text-blue-600 hover:text-blue-500"
                >
                  + Add Page
                </button>
              </div>
              {pages.balance.map((page, index) => (
                <div key={index} className="flex gap-2">
                  <input
                    type="number"
                    value={page}
                    onChange={(e) => handlePageChange('balance', index, e.target.value)}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    placeholder="Page number"
                  />
                  <button
                    type="button"
                    onClick={() => removePage('balance', index)}
                    className="text-red-600 hover:text-red-500"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>

            {/* Cash Flow Pages */}
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <label className="block text-sm font-medium text-gray-700">
                  Cash Flow Pages
                </label>
                <button
                  type="button"
                  onClick={() => addPage('cashFlow')}
                  className="text-sm text-blue-600 hover:text-blue-500"
                >
                  + Add Page
                </button>
              </div>
              {pages.cashFlow.map((page, index) => (
                <div key={index} className="flex gap-2">
                  <input
                    type="number"
                    value={page}
                    onChange={(e) => handlePageChange('cashFlow', index, e.target.value)}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    placeholder="Page number"
                  />
                  <button
                    type="button"
                    onClick={() => removePage('cashFlow', index)}
                    className="text-red-600 hover:text-red-500"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex justify-center">
            <button
              onClick={handleSubmit}
              disabled={loading || !files.pdf || !files.excel}
              className={clsx(
                "inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm",
                "focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500",
                loading || !files.pdf || !files.excel
                  ? "bg-gray-300 cursor-not-allowed"
                  : "bg-blue-600 hover:bg-blue-700 text-white"
              )}
            >
              {loading ? (
                "Processing..."
              ) : (
                <>
                  <ArrowDownTrayIcon className="mr-2 h-5 w-5" />
                  Process Files
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;